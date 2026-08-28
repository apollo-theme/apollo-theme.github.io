from __future__ import annotations

import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from urllib.parse import unquote_to_bytes

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"


class PaletteContractTests(unittest.TestCase):
    def test_site_palette_matches_pinned_canonical_hash(self) -> None:
        site_palette = ROOT / "palette" / "apollo.json"
        self.assertTrue(site_palette.is_file(), "palette/apollo.json must exist")
        self.assertEqual(
            hashlib.sha256(site_palette.read_bytes()).hexdigest(), EXPECTED_SHA256
        )

    def test_palette_exposes_complete_terminal_tables(self) -> None:
        palette = json.loads((ROOT / "palette" / "apollo.json").read_text())
        self.assertEqual(len(palette["terminal"]["ansi"]), 8)
        self.assertEqual(len(palette["terminal"]["bright"]), 8)
        self.assertEqual(
            palette["constraints"]["restrictedColors"]["#665c54"],
            "ANSI bright black only; never use for normal or small interface text.",
        )

    def test_generator_maps_palette_roles_semantically(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("site_generate", ROOT / "scripts" / "generate.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        palette = module.load_palette()
        base, ansi, bright = module.palette_tables(palette)
        colors = palette["colors"]
        self.assertEqual(
            base,
            (
                ("Canvas", colors["background"]),
                ("Raised", colors["surface"]),
                ("Primary", colors["foreground"]),
                ("Secondary", colors["foregroundSecondary"]),
                ("Inactive", colors["foregroundInactive"]),
                ("Focus", colors["accent"]),
                ("Selection", colors["selection"]),
                ("Danger", colors["danger"]),
                ("Success", colors["success"]),
                ("Info", colors["info"]),
                ("Magenta", colors["magenta"]),
                ("Cyan", colors["cyan"]),
            ),
        )
        names = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")
        self.assertEqual(ansi, tuple(zip(names, palette["terminal"]["ansi"], strict=True)))
        self.assertEqual(
            bright,
            tuple(
                zip(
                    (f"Bright {name.lower()}" for name in names),
                    palette["terminal"]["bright"],
                    strict=True,
                )
            ),
        )


EXPECTED_SLUGS = [
    "sonicterm", "wezterm", "iterm2", "apple-terminal", "alacritty",
    "windows-terminal", "firefox", "vscode", "visual-studio", "vim",
    "nvim", "xcode", "tmux", "rmux", "powershell", "bat", "eza",
]


class GeneratedSiteTests(unittest.TestCase):
    def test_generated_site_has_exact_permanent_app_inventory(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        ids = [f'id="app-{slug}"' for slug in EXPECTED_SLUGS]
        self.assertEqual(sum(html.count(app_id) for app_id in ids), 17)
        self.assertFalse(any(
            f'id="app-{slug}"' not in html for slug in EXPECTED_SLUGS
        ))
        self.assertEqual(
            sorted(path.stem for path in (ROOT / "previews").glob("*.svg")),
            sorted(EXPECTED_SLUGS),
        )

    def test_previews_are_safe_social_graphics_with_varied_layouts(self) -> None:
        layouts: set[str] = set()
        for slug in EXPECTED_SLUGS:
            svg = (ROOT / "previews" / f"{slug}.svg").read_text(encoding="utf-8")
            self.assertIn('width="1200" height="630"', svg)
            self.assertIn("SIMULATED PREVIEW", svg)
            self.assertIn("<style>", svg)
            self.assertNotIn("<script", svg.lower())
            self.assertNotIn('href="http://', svg)
            self.assertNotIn("<image", svg.lower())
            marker = re.search(r'<g class="layout layout-([a-z-]+)">', svg)
            self.assertIsNotNone(marker)
            assert marker is not None
            layouts.add(marker.group(1))
        self.assertGreaterEqual(len(layouts), 8)

    def test_preview_styles_use_canonical_palette_roles(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("site_generate_preview", ROOT / "scripts" / "generate.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        palette = module.load_palette()
        colors = palette["colors"]
        svg = module.render_preview(module.APPS[0], palette)
        style = svg.split("<style>", 1)[1].split("</style>", 1)[0]
        expected_fills = {
            "body": colors["foreground"],
            "bright": colors["foregroundBright"],
            "dim": colors["foregroundSecondary"],
            "label": colors["foregroundSecondary"],
            "accent": colors["accent"],
            "success": colors["success"],
            "info": colors["info"],
            "line-number": colors["foregroundInactive"],
            "canvas-text": colors["background"],
            "stamp": colors["background"],
            "title-small": colors["foregroundBright"],
        }
        for selector, color in expected_fills.items():
            self.assertRegex(style, rf'\.{re.escape(selector)}\{{fill:{re.escape(color)}[;}}]')
        self.assertNotRegex(style, r'\.dim\{fill:#928374[;}]')


    def test_site_contains_required_content_links_and_accessibility_hooks(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for slug in EXPECTED_SLUGS:
            repo = f"https://github.com/apollo-theme/{slug}-apollo-theme"
            self.assertIn(f'href="{repo}"', html)
            self.assertIn(f'href="{repo}#readme"', html)
            self.assertIn(f'href="{repo}/releases/latest"', html)
            self.assertIn(
                f'src="previews/{slug}.svg"',
                html,
            )
        self.assertIn('href="#main"', html)
        self.assertIn('class="skip-link"', html)
        self.assertIn('aria-label="Primary"', html)
        self.assertIn('href="palette/apollo.json"', html)
        self.assertIn('href="LICENSE"', html)
        self.assertIn("Gruvbox", html)
        self.assertIn("SonicTerm", html)
        self.assertIn('rel="license"', html)
        favicon = re.search(r'<link rel="icon" href="([^"]+)">', html)
        self.assertIsNotNone(favicon)
        assert favicon is not None
        href = favicon.group(1)
        prefix = "data:image/svg+xml,"
        self.assertTrue(href.startswith(prefix))
        self.assertIsNone(re.search(r"\s", href))
        favicon_root = ET.fromstring(unquote_to_bytes(href[len(prefix):]).decode("utf-8"))
        self.assertEqual(favicon_root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(favicon_root.get("viewBox"), "0 0 64 64")
        palette = json.loads((ROOT / "palette" / "apollo.json").read_text())
        children = list(favicon_root)
        self.assertEqual([child.tag for child in children], ["{http://www.w3.org/2000/svg}rect", "{http://www.w3.org/2000/svg}path"])
        self.assertEqual(children[0].get("fill"), palette["colors"]["background"])
        self.assertEqual(children[1].get("fill"), palette["colors"]["accent"])
        self.assertNotIn("analytics", html.lower())
        self.assertNotIn("<script", html.lower())

    def test_site_shows_complete_palette_tables(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        palette = json.loads((ROOT / "palette" / "apollo.json").read_text())
        required = [
            palette["colors"][key]
            for key in (
                "background", "surface", "foreground", "foregroundSecondary",
                "foregroundInactive", "accent", "selection", "danger", "success",
                "info", "magenta", "cyan",
            )
        ] + palette["terminal"]["ansi"] + palette["terminal"]["bright"]
        for color in required:
            self.assertIn(color, html)
        self.assertIn("Base palette", html)
        self.assertIn("ANSI", html)
        self.assertIn("Bright", html)


    def test_css_encodes_responsive_accessible_instrument_surface(self) -> None:
        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        for token in ("#141617", "#1d2021", "#cfbc97", "#d5c4a1", "#928374", "#fabd2f", "#3c3836"):
            self.assertIn(token, css)
        self.assertIn(":focus-visible", css)
        self.assertIn("min-height:44px", css.replace(" ", ""))
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("@media (max-width: 767px)", css)
        self.assertIn("overflow-x:hidden", css)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("backdrop-filter", css)
        self.assertNotIn("#665c54", css)



class RepositoryContractTests(unittest.TestCase):
    def test_test_suite_is_repository_hermetic(self) -> None:
        source = (ROOT / "tests" / "test_site.py").read_text(encoding="utf-8")
        self.assertNotIn("/" + "Users/", source)

    def test_required_repository_files_and_pinned_ci_exist(self) -> None:
        required = (
            ".nojekyll", "LICENSE", "CLAUDE.md", "README.md", "index.html",
            "assets/site.css", "palette/apollo.json", "scripts/generate.py",
            "scripts/check.py", ".github/workflows/pages.yml",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
        self.assertIn("python3 scripts/check.py", workflow)
        for sha in (
            "11bd71901bbe5b1630ceea73d27597364c9af683",
            "a26af69be951a213d495a4c3e4e4022e16d87065",
            "983d7736d9b0ae728b81ab479565c72886d7745b",
            "56afc609e74202658d3ffba0e8f6dda462b719fa",
            "d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e",
        ):
            self.assertIn(sha, workflow)
        self.assertNotRegex(workflow, r"uses: [^\n]+@v\d")

    def test_generation_check_mode_detects_no_drift(self) -> None:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
