from __future__ import annotations

import argparse
import difflib
import html
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import quote
import json

ROOT = Path(__file__).resolve().parents[1]
ORG = "https://github.com/apollo-theme"


@dataclass(frozen=True)
class App:
    slug: str
    name: str
    family: str
    layout: str
    tagline: str
    lines: tuple[str, ...]

    @property
    def repo(self) -> str:
        return f"{ORG}/{self.slug}-apollo-theme"


APPS = (
    App("sonicterm", "SonicTerm", "terminal", "flight-console", "The reference shell keeps the signal visible.", ("apollo main", "$ python3 scripts/check.py", "palette ........ exact", "previews ....... 17 / 17", "$ _")),
    App("wezterm", "WezTerm", "terminal", "split-shell", "Lua tabs and panes on one flight deck.", ("$ wezterm cli list", "WIN TAB PANE TITLE", "0   0   0    theme", "return { color_scheme = 'Apollo' }")),
    App("iterm2", "iTerm2", "terminal", "split-shell", "A macOS split session with a quiet profile rail.", ("$ git status --short", " M assets/site.css", "?? previews/", "Profile: Apollo")),
    App("apple-terminal", "Apple Terminal", "terminal", "native-shell", "The native terminal reduced to the essential readout.", ("Last login: Thu 20:14", "apollo@flight-deck % sw_vers", "ProductName: macOS", "BuildVersion: APOLLO")),
    App("alacritty", "Alacritty", "terminal", "native-shell", "GPU-accelerated output without competing chrome.", ("$ hyperfine scripts/check.py", "Time (mean ± σ): 84.2 ms", "Range: 81.8 … 89.1 ms", "$ _")),
    App("windows-terminal", "Windows Terminal", "terminal", "tabbed-shell", "PowerShell tabs, search, and command feedback.", ("PS C:\\apollo> Get-ChildItem", "d---- previews", "d---- scripts", "-a--- index.html")),
    App("firefox", "Firefox", "browser", "browser-chrome", "Browser chrome and web surfaces carry the same semantic signal.", ("apollo-theme.github.io", "General", "Extensions & Themes", "Enable Apollo")),
    App("vscode", "VS Code", "editor", "code-workbench", "Explorer, source, diagnostics, and status in balance.", ("def render_preview(app):", "    palette = load_palette()", "    return SVG.format(", "        accent='#fabd2f')")),
    App("visual-studio", "Visual Studio", "editor", "ide-inspector", "A dense IDE surface with legible hierarchy.", ("public sealed class ThemeService", "public string Accent => '#fabd2f';", "public bool IsDark => true;", "Build succeeded. 0 warnings")),
    App("vim", "Vim", "editor", "modal-source", "Modal state stays unmistakable.", ("set background=dark", "hi Normal guifg=#cfbc97", "let g:colors_name = 'apollo'", ":set cursorline")),
    App("nvim", "Neovim", "editor", "code-workbench", "A Lua workspace with tree, source, and diagnostics.", ("local M = {}", "M.canvas = '#141617'", "M.focus = '#fabd2f'", "vim.api.nvim_set_hl(0, 'Normal')")),
    App("xcode", "Xcode", "editor", "ide-inspector", "Navigator, source, inspector, and console on one plane.", ("struct ApolloTheme {", "static let canvas = 0x141617", "static let focus = 0xfabd2f", "Build Succeeded")),
    App("tmux", "tmux", "multiplexer", "pane-grid", "Three shell contexts joined by a clear status rail.", ("0:editor", "1:tests", "2:server", "[apollo] 20:14")),
    App("rmux", "RMUX", "multiplexer", "mission-board", "Session orchestration as a compact mission board.", ("● apollo-site", "3 panes · 1 active", "34 previews verified", "Dark + Light viewport pass complete")),
    App("powershell", "PowerShell", "shell", "object-table", "Structured command output with unmistakable state.", ("Get-ApolloPort | Where Status -eq Ready", "Name          Family       Status", "SonicTerm     Terminal     Ready", "Firefox       Browser      Ready")),
    App("bat", "bat", "utility", "source-listing", "Source output with line, syntax, and change context.", ("118 def render_app(app):", "119     repo = app.repo", "120     return TEMPLATE.format(", "121         label='SIMULATED')")),
    App("eza", "eza", "utility", "file-table", "File metadata aligned for a fast visual scan.", ("drwx  544B  --  assets/", "drwx  2.1k  --  palette/", "drwx   18k   N  previews/", "-rw-   42k   M  index.html")),
)
SLUGS = tuple(app.slug for app in APPS)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def txt(x: int, y: int, value: str, cls: str = "body", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{esc(value)}</text>'


def box(x: int, y: int, width: int, height: int, cls: str = "panel") -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" class="{cls}"/>'


def line(x1: int, y1: int, x2: int, y2: int, cls: str = "rule") -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'


def rows(x: int, y: int, values: tuple[str, ...], step: int = 45) -> str:
    classes = ("bright", "info", "body", "success", "accent")
    return "".join(txt(x, y + index * step, value, classes[min(index, 4)]) for index, value in enumerate(values))


def public_appearance_name(appearance: str) -> str:
    return "Apollo Light" if appearance == "light" else "Apollo Dark"


def public_appearance_stamp(appearance: str) -> str:
    return "APOLLO LIGHT" if appearance == "light" else "APOLLO DARK"


def native_appearance_name(appearance: str) -> str:
    return "Apollo Light" if appearance == "light" else "Apollo"


def native_appearance_stamp(appearance: str) -> str:
    return "APOLLO LIGHT" if appearance == "light" else "APOLLO"


def render_scene(app: App, appearance: str = "dark") -> str:
    parts: list[str] = []
    native_name = native_appearance_name(appearance)
    native_stamp = native_appearance_stamp(appearance)
    if app.layout == "flight-console":
        parts += [box(70, 142, 740, 366), box(830, 142, 300, 366, "raised"), line(70, 190, 810, 190), txt(94, 174, "MISSION SHELL", "label"), rows(104, 234, app.lines, 50), txt(854, 174, "SIGNAL", "label"), line(854, 220, 1104, 220, "signal"), '<circle cx="854" cy="220" r="6" class="node"/><circle cx="979" cy="220" r="6" class="node"/><circle cx="1104" cy="220" r="6" class="live"/>', txt(854, 275, "FOCUS", "dim"), box(1030, 255, 60, 25, "focus"), txt(854, 325, "INFO", "dim"), box(1030, 305, 60, 25, "info-box"), txt(854, 375, "SUCCESS", "dim"), box(1030, 355, 60, 25, "success-box"), txt(854, 435, "CURSOR", "dim"), txt(1090, 435, "READY", "success", "end")]
    elif app.layout == "split-shell":
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 45, "raised"), box(86, 151, 250, 36, "selected"), txt(106, 176, app.name, "bright"), txt(362, 176, "server", "dim"), line(620, 187, 620, 508), txt(94, 224, "LOCAL", "label"), rows(104, 270, app.lines[:3]), txt(646, 224, "PROFILE / CONFIG", "label"), rows(656, 270, app.lines[3:]), box(70, 484, 1060, 24, "status"), txt(88, 502, "apollo/theme · pane 1 of 2", "canvas-text")]
    elif app.layout in {"native-shell", "tabbed-shell"}:
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 45, "raised"), txt(92, 172, f"{app.name} — {native_name}", "dim"), rows(104, 236, app.lines, 53), box(850, 210, 250, 180, "raised"), txt(874, 242, "PROFILE", "label"), txt(874, 286, "Text", "dim"), txt(1074, 286, native_name, "body", "end"), txt(874, 330, "Cursor", "dim"), box(1044, 310, 30, 24, "focus"), txt(874, 374, "Status", "dim"), txt(1074, 374, "READY", "success", "end")]
    elif app.layout == "browser-chrome":
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 76, "raised"), box(92, 152, 224, 28, "selected"), txt(106, 172, "Apollo Theme", "bright"), txt(102, 204, "‹  ›  ↻", "dim"), box(190, 185, 760, 24, "selected"), txt(208, 204, app.lines[0], "body"), box(70, 218, 224, 290, "raised"), txt(96, 254, "FIREFOX", "label"), txt(96, 303, app.lines[1], "body"), txt(96, 350, app.lines[2], "bright"), txt(324, 266, f"{native_stamp} / {'DAY FLIGHT' if appearance == 'light' else 'NIGHT FLIGHT'}", "title-small"), txt(324, 304, app.tagline, "dim"), box(324, 342, 160, 110, "swatch-canvas"), box(500, 342, 160, 110, "swatch-surface"), box(676, 342, 160, 110, "focus"), box(852, 342, 160, 110, "info-box"), box(852, 468, 160, 30, "focus"), txt(932, 489, app.lines[3], "canvas-text", "middle")]
    elif app.layout in {"code-workbench", "ide-inspector"}:
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 42, "raised"), txt(92, 170, "File  Edit  View  Git  Run  Terminal", "dim"), box(70, 184, 236, 300, "raised"), txt(94, 218, "EXPLORER", "label"), txt(94, 262, "▾ APOLLO", "body"), txt(114, 304, "▾ source", "dim"), txt(134, 346, "theme", "bright"), txt(114, 388, "palette.json", "dim"), txt(94, 448, "OUTLINE", "label"), box(306, 184, 824, 300), txt(332, 218, f"{app.name} / theme source", "label"), rows(342, 268, app.lines, 48), box(70, 484, 1060, 24, "status"), txt(88, 502, "main*", "canvas-text"), txt(1112, 502, "UTF-8 · Ln 14", "canvas-text", "end")]
    elif app.layout == "modal-source":
        parts += [box(70, 142, 1060, 366), "".join(txt(94, 190+i*44, str(i+1), "line-number") for i in range(7)), rows(150, 190, app.lines, 65), box(70, 462, 1060, 25, "status"), txt(88, 480, " NORMAL ", "canvas-text"), txt(220, 480, "apollo.vim [+]", "canvas-text"), txt(1110, 480, "100%", "canvas-text", "end"), txt(88, 510, app.lines[-1], "accent")]
    elif app.layout == "pane-grid":
        parts += [box(70, 142, 1060, 366), line(650, 142, 650, 484), line(650, 326, 1130, 326), txt(94, 178, app.lines[0], "label"), txt(680, 178, app.lines[1], "label"), txt(680, 362, app.lines[2], "label"), txt(104, 240, "$ nvim index.html", "bright"), txt(104, 292, "17 sections ready", "success"), txt(680, 240, "$ python3 scripts/check.py", "bright"), txt(680, 292, "all checks passed", "success"), txt(680, 424, "$ python3 -m http.server", "bright"), box(70, 484, 1060, 24, "status"), txt(88, 502, app.lines[3], "canvas-text")]
    elif app.layout == "mission-board":
        parts += [box(70, 142, 1060, 366), box(70, 142, 226, 366, "raised"), txt(94, 180, "RMUX / SESSIONS", "label"), box(88, 202, 190, 46, "selected"), txt(104, 232, app.lines[0], "bright"), txt(104, 286, app.lines[1], "body"), txt(104, 342, "○ docs", "dim"), box(296, 142, 834, 342), txt(322, 180, "MISSION CONTROL", "label"), box(318, 210, 380, 240), box(720, 210, 386, 105, "raised"), box(720, 337, 386, 113, "raised"), txt(342, 250, "PRIMARY", "label"), txt(342, 304, "$ ./scripts/check.py", "bright"), txt(342, 358, app.lines[2], "success"), txt(744, 250, "WATCH", "label"), txt(744, 290, "assets/site.css clean", "success"), txt(744, 377, "NOTES", "label"), txt(744, 421, app.lines[3], "accent"), box(296, 484, 834, 24, "status"), txt(316, 502, "CTRL+A panes · CTRL+G sessions", "canvas-text")]
    elif app.layout == "object-table":
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 45, "raised"), txt(94, 172, "APOLLO POWERSHELL · OBJECT PIPELINE", "label"), rows(98, 228, app.lines, 56), txt(98, 454, "Ready objects retain type, state, and contrast.", "dim"), box(70, 484, 1060, 24, "status"), txt(88, 502, "PS 7.5 · UTF-8 · APOLLO", "canvas-text")]
    elif app.layout == "source-listing":
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 45, "raised"), txt(94, 172, "File: scripts/generate.py", "bright"), box(70, 187, 14, 297, "success-box"), rows(108, 236, app.lines, 57), box(70, 484, 1060, 24, "status"), txt(88, 502, "──── changed · Python", "canvas-text")]
    else:
        parts += [box(70, 142, 1060, 366), box(70, 142, 1060, 45, "raised"), txt(94, 172, "eza --long --git --group-directories-first", "label"), txt(98, 226, "MODE   SIZE  GIT  NAME", "dim"), line(96, 244, 1104, 244), rows(98, 294, app.lines, 52), box(70, 484, 1060, 24, "status"), txt(88, 502, "6 entries · sorted directories first", "canvas-text")]
    return "".join(parts)


def app_for_appearance(app: App, palette: dict, appearance: str) -> App:
    if appearance != "light":
        return app
    colors = palette["colors"]
    line_transforms = {
        "sonicterm": {
            "apollo main": "apollo-light main",
        },
        "wezterm": {
            "return { color_scheme = 'Apollo' }": "return { color_scheme = 'Apollo Light' }",
        },
        "iterm2": {
            "Profile: Apollo": "Profile: Apollo Light",
        },
        "firefox": {
            "Enable Apollo": "Enable Apollo Light",
        },
        "vscode": {
            "    palette = load_palette()": "    palette = load_light_palette()",
            "        accent='#fabd2f')": f"        accent='{colors['accent']}')",
        },
        "visual-studio": {
            "public string Accent => '#fabd2f';": f"public string Accent => '{colors['accent']}';",
            "public bool IsDark => true;": "public bool IsDark => false;",
        },
        "vim": {
            "set background=dark": "set background=light",
            "hi Normal guifg=#cfbc97": f"hi Normal guifg={colors['foreground']}",
            "let g:colors_name = 'apollo'": "let g:colors_name = 'apollo-light'",
        },
        "nvim": {
            "M.canvas = '#141617'": f"M.canvas = '{colors['background']}'",
            "M.focus = '#fabd2f'": f"M.focus = '{colors['accent']}'",
        },
        "xcode": {
            "static let canvas = 0x141617": f"static let canvas = 0x{colors['background'][1:]}",
            "static let focus = 0xfabd2f": f"static let focus = 0x{colors['accent'][1:]}",
        },
        "tmux": {
            "[apollo] 20:14": "[apollo-light] 20:14",
        },
    }
    transforms = line_transforms.get(app.slug, {})
    lines = tuple(transforms.get(line, line) for line in app.lines)
    return replace(app, lines=lines)


def render_preview(app: App, palette: dict, appearance: str = "dark") -> str:
    displayed_app = app_for_appearance(app, palette, appearance)
    scene = render_scene(displayed_app, appearance)
    colors = palette["colors"]
    public_name = public_appearance_name(appearance)
    public_stamp = public_appearance_stamp(appearance)
    styles = (
        f'.canvas{{fill:{colors["background"]}}}.frame,.panel{{fill:{colors["background"]};stroke:{colors["selection"]};stroke-width:1}}'
        f'.raised,.toolbar{{fill:{colors["surface"]};stroke:{colors["selection"]};stroke-width:1}}'
        ".body,.bright,.dim,.label,.accent,.success,.info,.line-number,.canvas-text,.stamp,.title-small{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
        f'.body{{fill:{colors["foreground"]};font-size:18px}}.bright{{fill:{colors["foregroundBright"]};font-size:18px}}'
        f'.dim{{fill:{colors["foregroundSecondary"]};font-size:16px}}.label{{fill:{colors["foregroundSecondary"]};font-size:14px;font-weight:700;letter-spacing:1.5px}}'
        f'.stamp{{fill:{colors["background"]};font-size:13px;font-weight:700;letter-spacing:1.5px}}'
        f'.accent{{fill:{colors["accent"]};font-size:18px}}.success{{fill:{colors["success"]};font-size:18px}}'
        f'.info{{fill:{colors["info"]};font-size:18px}}.line-number{{fill:{colors["foregroundInactive"]};font-size:15px}}'
        f'.canvas-text{{fill:{colors["background"]};font-size:15px;font-weight:700}}.title-small{{fill:{colors["foregroundBright"]};font-size:24px;font-weight:700}}'
        f'.rule{{stroke:{colors["selection"]};stroke-width:1}}.signal{{stroke:{colors["foregroundInactive"]};stroke-width:2}}.node{{fill:{colors["foregroundInactive"]}}}'
        f'.live,.focus{{fill:{colors["accent"]}}}.info-box{{fill:{colors["info"]}}}.success-box{{fill:{colors["success"]}}}'
        f'.status{{fill:{colors["accent"]}}}.selected{{fill:{colors["selection"]};stroke:{colors["foregroundInactive"]};stroke-width:1}}'
        f'.swatch-canvas{{fill:{colors["background"]};stroke:{colors["selection"]}}}.swatch-surface{{fill:{colors["surface"]};stroke:{colors["selection"]}}}'
    )
    chunks = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">',
        f'<title id="title">{public_name} for {esc(app.name)} — simulated preview</title>',
        f'<desc id="desc">A clearly labeled simulated {esc(app.name)} interface using the {public_name} color palette.</desc>',
        f'<style>{styles}</style>',
        '<rect width="1200" height="630" class="canvas"/>',
        '<rect x="40" y="40" width="1120" height="550" class="frame"/>',
        f'<rect x="40" y="40" width="1120" height="64" fill="{colors["surface"]}"/>',
        f'<rect x="914" y="57" width="214" height="30" fill="{colors["accent"]}"/>',
        txt(72, 80, f"{public_stamp} / {app.family.upper()}", "label"),
        txt(1021, 78, "SIMULATED PREVIEW", "stamp", "middle"),
        f'<g class="layout layout-{esc(app.layout)}">{scene}</g>',
        '<line x1="70" y1="548" x2="1130" y2="548" class="rule"/>',
        txt(70, 578, app.name, "bright"),
        txt(1130, 578, displayed_app.tagline, "dim", "end"),
        '</svg>',
    ]
    return "\n".join(chunks) + "\n"


def palette_cell(name: str, value: str, restricted: bool = False) -> str:
    flag = '<span class="restricted">ANSI only</span>' if restricted else ""
    return f'<li class="swatch"><span class="swatch-color" style="--swatch:{value}"></span><span class="swatch-name">{esc(name)}</span><code>{value}</code>{flag}</li>'


def render_app_section(app: App, index: int) -> str:
    repo = app.repo
    return f'''<section class="app-port" id="app-{app.slug}" aria-labelledby="title-{app.slug}">
<div class="port-copy"><p class="port-index">PORT {index:02d} / 17 · {esc(app.family.upper())}</p><h2 id="title-{app.slug}">{esc(app.name)}</h2><p>{esc(app.tagline)}</p><nav class="port-links" aria-label="{esc(app.name)} links"><a href="{repo}">Repository</a><a href="{repo}#readme">Install / README</a><a href="{repo}/releases/latest">Latest release</a></nav></div>
<div class="appearance-pair">
<figure class="preview preview-dark" id="app-{app.slug}-dark"><a class="preview-link" href="#app-{app.slug}-dark" aria-label="Link to {esc(app.name)} Apollo Dark appearance"><img src="previews/{app.slug}.svg" alt="Simulated {esc(app.name)} interface using Apollo Dark colors" width="1200" height="630" loading="lazy" decoding="async"></a><figcaption><span class="appearance-label">Apollo Dark</span><span>SIMULATED PREVIEW · illustrative Apollo Dark interface, not an application screenshot.</span></figcaption></figure>
<figure class="preview preview-light" id="app-{app.slug}-light"><a class="preview-link" href="#app-{app.slug}-light" aria-label="Link to {esc(app.name)} Apollo Light appearance"><img src="previews/{app.slug}-light.svg" alt="Simulated {esc(app.name)} interface using Apollo Light colors" width="1200" height="630" loading="lazy" decoding="async"></a><figcaption><span class="appearance-label">Apollo Light</span><span>SIMULATED PREVIEW · illustrative Apollo Light interface, not an application screenshot.</span></figcaption></figure>
</div>
</section>'''


def load_palette_file(filename: str) -> dict:
    return json.loads((ROOT / "palette" / filename).read_text(encoding="utf-8"))


def load_palette() -> dict:
    return load_palette_file("apollo.json")


def load_light_palette() -> dict:
    return load_palette_file("apollo-light.json")


def palette_tables(palette: dict) -> tuple[tuple[tuple[str, str], ...], ...]:
    colors = palette["colors"]
    terminal = palette["terminal"]
    base = (
        ("Canvas", colors["background"]), ("Raised", colors["surface"]),
        ("Primary", colors["foreground"]), ("Secondary", colors["foregroundSecondary"]),
        ("Inactive", colors["foregroundInactive"]), ("Focus", colors["accent"]),
        ("Selection", colors["selection"]), ("Danger", colors["danger"]),
        ("Success", colors["success"]), ("Info", colors["info"]),
        ("Magenta", colors["magenta"]), ("Cyan", colors["cyan"]),
    )
    names = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")
    ansi = tuple(zip(names, terminal["ansi"], strict=True))
    bright = tuple(zip((f"Bright {name.lower()}" for name in names), terminal["bright"], strict=True))
    return base, ansi, bright


def render_palette_article(
    palette_id: str, filename: str, palette: dict, public_name: str
) -> str:
    base, ansi, bright = palette_tables(palette)
    restricted = set(palette["constraints"]["restrictedColors"])
    base_cells = "".join(palette_cell(name, value, value in restricted) for name, value in base)
    ansi_cells = "".join(palette_cell(name, value, value in restricted) for name, value in ansi)
    bright_cells = "".join(palette_cell(name, value, value in restricted) for name, value in bright)
    return f'''<article class="palette-table" id="{palette_id}" aria-labelledby="{palette_id}-title">
<div class="palette-table-heading"><p class="appearance-kicker">{esc(public_name)} appearance</p><h3 id="{palette_id}-title">{esc(public_name)}</h3><a href="palette/{filename}">Open canonical JSON</a></div>
<div class="palette-group"><h4>Base palette</h4><ul class="palette-strip base-strip">{base_cells}</ul></div>
<div class="palette-group"><h4>ANSI</h4><ul class="palette-strip">{ansi_cells}</ul></div>
<div class="palette-group"><h4>Bright</h4><ul class="palette-strip">{bright_cells}</ul></div>
</article>'''


def render_index() -> str:
    palette = load_palette()
    light_palette = load_light_palette()
    colors = palette["colors"]
    light_colors = light_palette["colors"]
    favicon = quote(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" fill="{colors["background"]}"/>'
        f'<path d="M16 48 30 14h6l14 34h-8l-3-8H27l-3 8Zm14-15h6l-3-9Z" fill="{colors["accent"]}"/>'
        '</svg>',
        safe="",
    )
    palette_articles = "".join((
        render_palette_article("palette-dark", "apollo.json", palette, "Apollo Dark"),
        render_palette_article("palette-light", "apollo-light.json", light_palette, "Apollo Light"),
    ))
    ports = "".join(render_app_section(app, index) for index, app in enumerate(APPS, 1))
    app_nav = "".join(f'<a href="#app-{app.slug}">{esc(app.name)}</a>' for app in APPS)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><meta name="theme-color" content="{colors["background"]}" media="(prefers-color-scheme: dark)"><meta name="theme-color" content="{light_colors["background"]}" media="(prefers-color-scheme: light)"><meta name="description" content="Apollo Dark and Apollo Light carry accessible Gruvbox palettes into 17 terminals, editors, browsers, and shell tools."><title>Apollo Dark + Apollo Light</title><link rel="icon" href="data:image/svg+xml,{favicon}"><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to main content</a><header class="site-header"><a class="wordmark" href="#top" aria-label="Apollo Theme home"><span aria-hidden="true">A/</span> APOLLO</a><nav aria-label="Primary"><a href="#palette">Palettes</a><a href="#ports">17 ports</a><a href="https://github.com/apollo-theme/apollo-theme">Source</a></nav></header>
<main id="main" tabindex="-1"><section class="hero" id="top" aria-labelledby="hero-title"><p class="eyebrow">GRUVBOX COLOR SYSTEM · DARK + LIGHT · HIGH-CONTRAST</p><h1 id="hero-title">Apollo Dark + Apollo Light.<br>Every instrument.</h1><p class="thesis">Apollo Dark and Apollo Light carry one semantic signal across the interfaces where work happens—without losing state, syntax, or focus between night and day.</p><div class="hero-actions"><a class="primary-action" href="#palette">Read both signals</a><a href="https://github.com/apollo-theme/apollo-theme">Canonical source</a></div></section>
<section class="signal-path" aria-label="Apollo signal path"><div class="signal-line"><span class="signal-node live"></span><span class="signal-node"></span><span class="signal-node"></span><span class="signal-node"></span></div><ol><li><strong>01 / SOURCE</strong><span>two palettes</span></li><li><strong>02 / MAP</strong><span>semantic roles</span></li><li><strong>03 / PORT</strong><span>17 repositories</span></li><li><strong>04 / RUN</strong><span>dark + light</span></li></ol></section>
<section class="palette-section" id="palette" aria-labelledby="palette-title"><div class="section-heading"><p class="eyebrow">TWO SOURCES OF TRUTH / SCHEMA 1</p><h2 id="palette-title">Color telemetry</h2><p>Compare the canonical <a href="#palette-dark">Apollo Dark</a> and <a href="#palette-light">Apollo Light</a> tables. Restricted ANSI colors never carry body text.</p></div><div class="palette-pair">{palette_articles}</div></section>
<section class="ports" id="ports" aria-labelledby="ports-title"><div class="section-heading"><p class="eyebrow">PORT MANIFEST / 17 PERMANENT TARGETS / 34 VIEWS</p><h2 id="ports-title">Apollo Dark and Apollo Light across every port.</h2><p>Every app shows Apollo Dark and Apollo Light side by side as explicit simulations. Neither appearance is hidden by your operating-system preference.</p></div><nav class="port-jump" aria-label="App sections">{app_nav}</nav>{ports}</section>
<section class="source-section" aria-labelledby="source-title"><p class="eyebrow">OPEN SYSTEM / MIT</p><h2 id="source-title">Inspect the source before you fly.</h2><p>Every port traces back to <a href="https://github.com/apollo-theme/apollo-theme">the canonical repository</a>, the exact <a href="palette/apollo.json">Apollo Dark JSON</a> and <a href="palette/apollo-light.json">Apollo Light JSON</a>, plus an <a href="LICENSE" rel="license">MIT license</a>.</p></section>
<section class="credits" aria-labelledby="credits-title"><p class="eyebrow">LINEAGE / THANKS</p><h2 id="credits-title">Built on a well-lit lineage.</h2><p>Thank you to <a href="https://github.com/morhetz/gruvbox">Gruvbox</a> for both color languages and <a href="https://github.com/D0n9X1n/SonicTerm">SonicTerm</a> for the near-black flight deck that became Apollo’s dark starting point.</p></section></main>
<footer><span>APOLLO THEME · 2026</span><a href="#top">Return to top</a></footer></body></html>
'''


def generated_files() -> dict[Path, str]:
    dark_palette = load_palette()
    light_palette = load_light_palette()
    files = {ROOT / "index.html": render_index()}
    files.update({ROOT / "previews" / f"{app.slug}.svg": render_preview(app, dark_palette) for app in APPS})
    files.update({
        ROOT / "previews" / f"{app.slug}-light.svg": render_preview(app, light_palette, "light")
        for app in APPS
    })
    return files


def check_generated(files: dict[Path, str]) -> bool:
    clean = True
    expected = {path for path in files if path.parent == ROOT / "previews"}
    actual = set((ROOT / "previews").glob("*.svg")) if (ROOT / "previews").exists() else set()
    for extra in sorted(actual - expected):
        print(f"unexpected generated file: {extra.relative_to(ROOT)}", file=sys.stderr)
        clean = False
    for path, wanted in files.items():
        found = path.read_text(encoding="utf-8") if path.exists() else ""
        if found != wanted:
            clean = False
            print(f"generated drift: {path.relative_to(ROOT)}", file=sys.stderr)
            diff = difflib.unified_diff(found.splitlines(), wanted.splitlines(), fromfile="committed", tofile="generated", n=1)
            for value in list(diff)[:24]:
                print(value, file=sys.stderr)
    return clean


def write_generated(files: dict[Path, str]) -> None:
    previews = ROOT / "previews"
    previews.mkdir(exist_ok=True)
    expected = {path for path in files if path.parent == previews}
    for extra in previews.glob("*.svg"):
        if extra not in expected:
            extra.unlink()
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Apollo site fixtures.")
    parser.add_argument("--check", action="store_true", help="fail when generated files have drifted")
    args = parser.parse_args()
    files = generated_files()
    if args.check:
        return 0 if check_generated(files) else 1
    write_generated(files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
