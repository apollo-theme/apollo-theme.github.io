#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote_to_bytes, urlparse

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "apollo.json": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light.json": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
EXPECTED_SLUGS = (
    "sonicterm", "wezterm", "iterm2", "apple-terminal", "alacritty",
    "windows-terminal", "firefox", "vscode", "visual-studio", "vim",
    "nvim", "xcode", "tmux", "rmux", "powershell", "bat", "eza",
)


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.images: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        if tag == "img":
            self.images.append(values)


def fail(message: str) -> None:
    raise AssertionError(message)


def luminance(color: str) -> float:
    values = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first: str, second: str) -> float:
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def load_palettes() -> dict[str, dict]:
    return {
        filename: json.loads((ROOT / "palette" / filename).read_text(encoding="utf-8"))
        for filename in EXPECTED_HASHES
    }


def check_palette() -> None:
    for filename, expected_hash in EXPECTED_HASHES.items():
        raw = (ROOT / "palette" / filename).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_hash:
            fail(f"{filename} hash mismatch: {digest}")
        data = json.loads(raw)
        if len(data["terminal"]["ansi"]) != 8 or len(data["terminal"]["bright"]) != 8:
            fail(f"{filename} must contain complete ANSI and bright tables")
        colors = data["colors"]
        canvas = colors["background"]
        for role in ("foreground", "foregroundSecondary", "foregroundInactive", "accent", "danger", "success", "info", "magenta", "cyan"):
            ratio = contrast(colors[role], canvas)
            if ratio < 4.5:
                fail(f"{filename} {role} contrast is {ratio:.2f}, below 4.5:1")
        for role, surface_role in (
            ("foregroundSecondary", "surface"),
            ("foreground", "selection"),
            ("background", "accent"),
            ("background", "danger"),
            ("background", "success"),
            ("background", "info"),
        ):
            ratio = contrast(colors[role], colors[surface_role])
            if ratio < 4.5:
                fail(f"{filename} {role}/{surface_role} contrast is {ratio:.2f}, below 4.5:1")
        if colors["ansiBrightBlack"] in data["constraints"]["restrictedColors"] and contrast(colors["ansiBrightBlack"], canvas) >= 4.5:
            fail(f"{filename} restricted bright black unexpectedly qualifies as body text")
        print(f"palette: {filename} exact sha256 {digest}; checked contrast pairs >= 4.5:1")


def decode_favicon(href: str) -> ET.Element:
    prefix = "data:image/svg+xml,"
    if not href.startswith(prefix) or re.search(r"\s", href):
        fail("site must contain a percent-encoded SVG favicon without whitespace")
    try:
        payload = unquote_to_bytes(href[len(prefix):]).decode("utf-8")
        root = ET.fromstring(payload)
    except (UnicodeDecodeError, ET.ParseError) as error:
        fail(f"favicon must decode to valid UTF-8 SVG: {error}")
    if root.tag != "{http://www.w3.org/2000/svg}svg" or root.get("viewBox") != "0 0 64 64":
        fail("favicon must use an SVG root with the expected viewBox")
    return root


def check_html() -> None:
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = SiteParser()
    parser.feed(text)
    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicates:
        fail(f"duplicate IDs: {duplicates}")
    app_ids = [value for value in parser.ids if value.startswith("app-")]
    expected_ids = [
        app_id
        for slug in EXPECTED_SLUGS
        for app_id in (f"app-{slug}", f"app-{slug}-dark", f"app-{slug}-light")
    ]
    if app_ids != expected_ids:
        fail(f"app IDs differ: {app_ids}")
    for palette_id in ("palette-dark", "palette-light"):
        if parser.ids.count(palette_id) != 1:
            fail(f"expected one {palette_id} anchor")
    known_ids = set(parser.ids)
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.scheme and parsed.scheme != "https":
            fail(f"non-HTTPS link: {link}")
        if not parsed.scheme and link.startswith("//"):
            fail(f"protocol-relative link: {link}")
        if link.startswith("#") and link[1:] not in known_ids:
            fail(f"broken fragment: {link}")
    expected_sources = [
        source
        for slug in EXPECTED_SLUGS
        for source in (f"previews/{slug}.svg", f"previews/{slug}-light.svg")
    ]
    if len(parser.images) != 34:
        fail(f"expected 34 preview images, found {len(parser.images)}")
    for source, image in zip(expected_sources, parser.images, strict=True):
        if not image.get("alt") or image.get("width") != "1200" or image.get("height") != "630":
            fail(f"preview lacks alt or exact dimensions: {image}")
        found = str(image.get("src", ""))
        if found != source:
            fail(f"preview source order differs: expected {source}, got {found}")
    if re.search(r"<(script|iframe)\b", text, re.I):
        fail("site must not require scripts or iframes")
    favicon = re.search(r'<link rel="icon" href="([^"]+)">', text)
    if not favicon:
        fail("site must contain an SVG favicon")
    favicon_root = decode_favicon(favicon.group(1))
    colors = json.loads((ROOT / "palette" / "apollo.json").read_text(encoding="utf-8"))["colors"]
    children = list(favicon_root)
    if len(children) != 2 or children[0].tag != "{http://www.w3.org/2000/svg}rect" or children[1].tag != "{http://www.w3.org/2000/svg}path":
        fail("favicon must contain the Apollo canvas and mark")
    if children[0].get("fill") != colors["background"] or children[1].get("fill") != colors["accent"]:
        fail("favicon colors must match canonical background and accent roles")
    print("html: semantic inventory, fragments, links, images, and favicon verified")


def check_svgs() -> None:
    files = sorted((ROOT / "previews").glob("*.svg"))
    expected_names = sorted(
        name
        for slug in EXPECTED_SLUGS
        for name in (f"{slug}.svg", f"{slug}-light.svg")
    )
    if [path.name for path in files] != expected_names:
        fail("preview SVG set differs from the exact 34-file app inventory")
    palettes = load_palettes()
    layouts: set[str] = set()
    for path in files:
        appearance = "light" if path.stem.endswith("-light") else "dark"
        filename = "apollo-light.json" if appearance == "light" else "apollo.json"
        colors = palettes[filename]["colors"]
        required_styles = (
            f'.canvas{{fill:{colors["background"]}}}',
            f'.raised,.toolbar{{fill:{colors["surface"]};',
            f'.body{{fill:{colors["foreground"]};',
            f'.dim{{fill:{colors["foregroundSecondary"]};',
            f'.line-number{{fill:{colors["foregroundInactive"]};',
            f'.live,.focus{{fill:{colors["accent"]}}}',
        )
        text = path.read_text(encoding="utf-8")
        if 'width="1200" height="630"' not in text:
            fail(f"wrong social dimensions: {path.name}")
        if "SIMULATED PREVIEW" not in text:
            fail(f"missing simulation label: {path.name}")
        if "<style>" not in text or re.search(r"<(script|image|foreignObject)\b", text, re.I):
            fail(f"unsafe or externally dependent SVG: {path.name}")
        for expected in required_styles:
            if expected not in text:
                fail(f"preview palette style drift in {path.name}: {expected}")
        match = re.search(r'<g class="layout layout-([a-z-]+)">', text)
        if not match:
            fail(f"missing standards-valid layout marker: {path.name}")
        layouts.add(match.group(1))
        if 'data-layout=' in text:
            fail(f"invalid SVG data-layout attribute: {path.name}")
        if appearance == "light" and "Apollo Light" not in text:
            fail(f"light preview lacks variant identity: {path.name}")
    if len(layouts) < 8:
        fail(f"previews need at least 8 meaningful layouts, found {len(layouts)}")
    print(f"svg: 34 safe simulations across {len(layouts)} layouts with exact variant styles")


def check_generated() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], cwd=ROOT)
    if result.returncode:
        fail("generated files have drifted")
    print("generated: no drift")


def run_tests() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        fail("unit tests failed")


def main() -> int:
    checks = (check_palette, check_html, check_svgs, check_generated, run_tests)
    try:
        for check in checks:
            check()
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: Apollo site checks complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
