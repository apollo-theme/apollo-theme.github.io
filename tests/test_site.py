from __future__ import annotations

import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET
import sys
from html import unescape
from pathlib import Path
from urllib.parse import unquote_to_bytes

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"
EXPECTED_LIGHT_SHA256 = "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763"


class PaletteContractTests(unittest.TestCase):
    def test_site_palette_matches_pinned_canonical_hash(self) -> None:
        site_palette = ROOT / "palette" / "apollo.json"
        self.assertTrue(site_palette.is_file(), "palette/apollo.json must exist")
        self.assertEqual(
            hashlib.sha256(site_palette.read_bytes()).hexdigest(), EXPECTED_SHA256
        )

    def test_site_light_palette_matches_pinned_canonical_hash(self) -> None:
        site_palette = ROOT / "palette" / "apollo-light.json"
        self.assertTrue(site_palette.is_file(), "palette/apollo-light.json must exist")
        self.assertEqual(
            hashlib.sha256(site_palette.read_bytes()).hexdigest(), EXPECTED_LIGHT_SHA256
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


EXPECTED_APPS = [
    ("sonicterm", "SonicTerm", "terminal"),
    ("wezterm", "WezTerm", "terminal"),
    ("iterm2", "iTerm2", "terminal"),
    ("apple-terminal", "Apple Terminal", "terminal"),
    ("alacritty", "Alacritty", "terminal"),
    ("windows-terminal", "Windows Terminal", "terminal"),
    ("firefox", "Firefox", "browser"),
    ("vscode", "VS Code", "editor"),
    ("visual-studio", "Visual Studio", "editor"),
    ("vim", "Vim", "editor"),
    ("nvim", "Neovim", "editor"),
    ("xcode", "Xcode", "editor"),
    ("tmux", "tmux", "multiplexer"),
    ("rmux", "RMUX", "multiplexer"),
    ("powershell", "PowerShell", "shell"),
    ("bat", "bat", "utility"),
    ("eza", "eza", "utility"),
]
EXPECTED_SLUGS = [slug for slug, _, _ in EXPECTED_APPS]


class GeneratedSiteTests(unittest.TestCase):
    def test_generated_site_has_exact_permanent_app_inventory(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        legacy_ids = [f'id="app-{slug}"' for slug in EXPECTED_SLUGS]
        self.assertEqual(sum(html.count(app_id) for app_id in legacy_ids), 17)
        self.assertFalse(any(
            f'id="app-{slug}"' not in html for slug in EXPECTED_SLUGS
        ))
        expected_previews = sorted(
            name
            for slug in EXPECTED_SLUGS
            for name in (f"{slug}.svg", f"{slug}-light.svg")
        )
        self.assertEqual(
            sorted(path.name for path in (ROOT / "previews").glob("*.svg")),
            expected_previews,
        )

    def test_each_app_exposes_visible_apollo_dark_and_light_appearances(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for slug, name, _ in EXPECTED_APPS:
            self.assertIn(f'id="app-{slug}-dark"', html)
            self.assertIn(f'id="app-{slug}-light"', html)
            self.assertIn(f'src="previews/{slug}.svg"', html)
            self.assertIn(f'src="previews/{slug}-light.svg"', html)
            self.assertIn(f'aria-label="Link to {name} Apollo Dark appearance"', html)
            self.assertIn(f'alt="Simulated {name} interface using Apollo Dark colors"', html)
            self.assertIn(f'aria-label="Link to {name} Apollo Light appearance"', html)
            self.assertIn(f'alt="Simulated {name} interface using Apollo Light colors"', html)
        self.assertEqual(
            html.count(
                "SIMULATED PREVIEW · illustrative Apollo Dark interface, not an application screenshot."
            ),
            17,
        )
        self.assertEqual(
            html.count(
                "SIMULATED PREVIEW · illustrative Apollo Light interface, not an application screenshot."
            ),
            17,
        )
        self.assertEqual(html.count(">Apollo Dark</span>"), 17)
        self.assertEqual(html.count(">Apollo Light</span>"), 17)
        self.assertIn("Apollo Dark and Apollo Light", html)

    def test_previews_are_safe_social_graphics_with_varied_layouts(self) -> None:
        layouts: set[str] = set()
        for slug in EXPECTED_SLUGS:
            for suffix in ("", "-light"):
                svg = (ROOT / "previews" / f"{slug}{suffix}.svg").read_text(encoding="utf-8")
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

    def test_light_preview_scene_text_matches_light_appearance(self) -> None:
        light_visual_studio = (ROOT / "previews" / "visual-studio-light.svg").read_text()
        light_vscode = (ROOT / "previews" / "vscode-light.svg").read_text()
        light_vim = (ROOT / "previews" / "vim-light.svg").read_text()
        light_nvim = (ROOT / "previews" / "nvim-light.svg").read_text()
        light_xcode = (ROOT / "previews" / "xcode-light.svg").read_text()
        self.assertIn("public bool IsDark =&gt; false;", light_visual_studio)
        self.assertIn("palette = load_light_palette()", light_vscode)
        self.assertIn("set background=light", light_vim)
        self.assertIn("hi Normal guifg=#3c3836", light_vim)
        self.assertIn("g:colors_name = &#x27;apollo-light&#x27;", light_vim)
        self.assertIn("M.canvas = &#x27;#f9f5d7&#x27;", light_nvim)
        self.assertIn("static let canvas = 0xf9f5d7", light_xcode)
        self.assertIn("static let focus = 0x8a5200", light_xcode)
        self.assertNotIn("background=dark", light_vim)
        self.assertNotIn("IsDark =&gt; true", light_visual_studio)
        self.assertNotIn("#141617", light_nvim)
        self.assertNotIn("0x141617", light_xcode)
        self.assertNotIn("0xfabd2f", light_xcode)

    def test_light_scene_transformations_are_exact_and_preserve_neutral_text(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "site_generate_light_lines", ROOT / "scripts" / "generate.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)

        expected_line_pairs = {
            "sonicterm": (
                ("apollo main", "apollo-light main"),
                ("$ python3 scripts/check.py", "$ python3 scripts/check.py"),
                ("palette ........ exact", "palette ........ exact"),
                ("previews ....... 17 / 17", "previews ....... 17 / 17"),
                ("$ _", "$ _"),
            ),
            "wezterm": (
                ("$ wezterm cli list", "$ wezterm cli list"),
                ("WIN TAB PANE TITLE", "WIN TAB PANE TITLE"),
                ("0   0   0    theme", "0   0   0    theme"),
                (
                    "return { color_scheme = 'Apollo' }",
                    "return { color_scheme = 'Apollo Light' }",
                ),
            ),
            "iterm2": (
                ("$ git status --short", "$ git status --short"),
                (" M assets/site.css", " M assets/site.css"),
                ("?? previews/", "?? previews/"),
                ("Profile: Apollo", "Profile: Apollo Light"),
            ),
            "apple-terminal": (
                ("Last login: Thu 20:14", "Last login: Thu 20:14"),
                ("apollo@flight-deck % sw_vers", "apollo@flight-deck % sw_vers"),
                ("ProductName: macOS", "ProductName: macOS"),
                ("BuildVersion: APOLLO", "BuildVersion: APOLLO"),
            ),
            "alacritty": (
                ("$ hyperfine scripts/check.py", "$ hyperfine scripts/check.py"),
                ("Time (mean ± σ): 84.2 ms", "Time (mean ± σ): 84.2 ms"),
                ("Range: 81.8 … 89.1 ms", "Range: 81.8 … 89.1 ms"),
                ("$ _", "$ _"),
            ),
            "windows-terminal": (
                ("PS C:\\apollo> Get-ChildItem", "PS C:\\apollo> Get-ChildItem"),
                ("d---- previews", "d---- previews"),
                ("d---- scripts", "d---- scripts"),
                ("-a--- index.html", "-a--- index.html"),
            ),
            "firefox": (
                ("apollo-theme.github.io", "apollo-theme.github.io"),
                ("General", "General"),
                ("Extensions & Themes", "Extensions & Themes"),
                ("Enable Apollo", "Enable Apollo Light"),
            ),
            "vscode": (
                ("def render_preview(app):", "def render_preview(app):"),
                ("    palette = load_palette()", "    palette = load_light_palette()"),
                ("    return SVG.format(", "    return SVG.format("),
                ("        accent='#fabd2f')", "        accent='#8a5200')"),
            ),
            "visual-studio": (
                ("public sealed class ThemeService", "public sealed class ThemeService"),
                (
                    "public string Accent => '#fabd2f';",
                    "public string Accent => '#8a5200';",
                ),
                ("public bool IsDark => true;", "public bool IsDark => false;"),
                ("Build succeeded. 0 warnings", "Build succeeded. 0 warnings"),
            ),
            "vim": (
                ("set background=dark", "set background=light"),
                ("hi Normal guifg=#cfbc97", "hi Normal guifg=#3c3836"),
                (
                    "let g:colors_name = 'apollo'",
                    "let g:colors_name = 'apollo-light'",
                ),
                (":set cursorline", ":set cursorline"),
            ),
            "nvim": (
                ("local M = {}", "local M = {}"),
                ("M.canvas = '#141617'", "M.canvas = '#f9f5d7'"),
                ("M.focus = '#fabd2f'", "M.focus = '#8a5200'"),
                (
                    "vim.api.nvim_set_hl(0, 'Normal')",
                    "vim.api.nvim_set_hl(0, 'Normal')",
                ),
            ),
            "xcode": (
                ("struct ApolloTheme {", "struct ApolloTheme {"),
                ("static let canvas = 0x141617", "static let canvas = 0xf9f5d7"),
                ("static let focus = 0xfabd2f", "static let focus = 0x8a5200"),
                ("Build Succeeded", "Build Succeeded"),
            ),
            "tmux": (
                ("0:editor", "0:editor"),
                ("1:tests", "1:tests"),
                ("2:server", "2:server"),
                ("[apollo] 20:14", "[apollo-light] 20:14"),
            ),
            "rmux": (
                ("● apollo-site", "● apollo-site"),
                ("3 panes · 1 active", "3 panes · 1 active"),
                ("34 previews verified", "34 previews verified"),
                (
                    "Dark + Light viewport pass complete",
                    "Dark + Light viewport pass complete",
                ),
            ),
            "powershell": (
                (
                    "Get-ApolloPort | Where Status -eq Ready",
                    "Get-ApolloPort | Where Status -eq Ready",
                ),
                ("Name          Family       Status", "Name          Family       Status"),
                ("SonicTerm     Terminal     Ready", "SonicTerm     Terminal     Ready"),
                ("Firefox       Browser      Ready", "Firefox       Browser      Ready"),
            ),
            "bat": (
                ("118 def render_app(app):", "118 def render_app(app):"),
                ("119     repo = app.repo", "119     repo = app.repo"),
                ("120     return TEMPLATE.format(", "120     return TEMPLATE.format("),
                ("121         label='SIMULATED')", "121         label='SIMULATED')"),
            ),
            "eza": (
                ("drwx  544B  --  assets/", "drwx  544B  --  assets/"),
                ("drwx  2.1k  --  palette/", "drwx  2.1k  --  palette/"),
                ("drwx   18k   N  previews/", "drwx   18k   N  previews/"),
                ("-rw-   42k   M  index.html", "-rw-   42k   M  index.html"),
            ),
        }
        self.assertEqual(set(expected_line_pairs), set(module.SLUGS))
        light_palette = module.load_light_palette()
        light_lines: list[str] = []
        for app in module.APPS:
            pairs = expected_line_pairs[app.slug]
            self.assertEqual(app.lines, tuple(dark for dark, _ in pairs), app.slug)
            displayed = module.app_for_appearance(app, light_palette, "light")
            self.assertEqual(
                displayed.lines,
                tuple(light for _, light in pairs),
                app.slug,
            )
            self.assertEqual(displayed.tagline, app.tagline, app.slug)
            light_lines.extend(displayed.lines)

        all_light_lines = "\n".join(light_lines)
        all_light_svgs = unescape("\n".join(
            (ROOT / "previews" / f"{slug}-light.svg").read_text(encoding="utf-8")
            for slug in module.SLUGS
        ))
        for corrupted in (
            "Get-Apollo LightPort",
            "struct Apollo LightTheme",
            "apollo-light-theme.github.io",
            "apollo-light@flight-deck",
            "PS C:\\apollo-light>",
            "● apollo-light-site",
        ):
            self.assertNotIn(corrupted, all_light_lines)
            self.assertNotIn(corrupted, all_light_svgs)
        for preserved in (
            "Get-ApolloPort",
            "struct ApolloTheme",
            "apollo-theme.github.io",
            "apollo@flight-deck",
            "PS C:\\apollo>",
            "● apollo-site",
        ):
            self.assertIn(preserved, all_light_lines)
            self.assertIn(preserved, all_light_svgs)

    def test_dark_compatibility_surfaces_keep_stable_names_and_native_identity(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for slug in EXPECTED_SLUGS:
            self.assertIn(f'id="app-{slug}"', html)
            self.assertIn(f'id="app-{slug}-dark"', html)
            self.assertIn(f'id="app-{slug}-light"', html)
            self.assertIn(f'src="previews/{slug}.svg"', html)
            self.assertTrue((ROOT / "previews" / f"{slug}.svg").is_file())

        dark_palette = json.loads((ROOT / "palette" / "apollo.json").read_text())
        dark_colors = dark_palette["colors"]
        wezterm = (ROOT / "previews" / "wezterm.svg").read_text()
        vim = (ROOT / "previews" / "vim.svg").read_text()
        firefox = (ROOT / "previews" / "firefox.svg").read_text()
        self.assertIn(f'.canvas{{fill:{dark_colors["background"]}}}', wezterm)
        self.assertIn(f'.body{{fill:{dark_colors["foreground"]};', wezterm)
        self.assertIn("color_scheme = &#x27;Apollo&#x27;", wezterm)
        self.assertIn("g:colors_name = &#x27;apollo&#x27;", vim)
        self.assertIn(">Apollo Theme</text>", firefox)
        self.assertNotIn("color_scheme = &#x27;Apollo Dark&#x27;", wezterm)
        self.assertNotIn("g:colors_name = &#x27;apollo-dark&#x27;", vim)
        self.assertNotIn(">Apollo Dark Theme</text>", firefox)

    def test_public_copy_and_previews_name_both_appearances_explicitly(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Apollo Dark + Apollo Light</title>", html)
        self.assertIn('content="Apollo Dark and Apollo Light ', html)
        self.assertIn('href="#palette-dark">Apollo Dark</a>', html)
        self.assertIn('href="#palette-light">Apollo Light</a>', html)
        self.assertIn('href="palette/apollo.json">Apollo Dark JSON</a>', html)
        self.assertIn('href="palette/apollo-light.json">Apollo Light JSON</a>', html)
        self.assertIn('id="palette-dark-title">Apollo Dark</h3>', html)
        self.assertIn('id="palette-light-title">Apollo Light</h3>', html)

        for slug, name, family in EXPECTED_APPS:
            for suffix, public_name, stamp in (
                ("", "Apollo Dark", "APOLLO DARK"),
                ("-light", "Apollo Light", "APOLLO LIGHT"),
            ):
                svg = (ROOT / "previews" / f"{slug}{suffix}.svg").read_text()
                self.assertIn(
                    f'<title id="title">{public_name} for {name} — simulated preview</title>',
                    svg,
                )
                self.assertIn(
                    f'<desc id="desc">A clearly labeled simulated {name} interface using the {public_name} color palette.</desc>',
                    svg,
                )
                self.assertIn(f'>{stamp} / {family.upper()}</text>', svg)

    def test_firefox_and_rmux_copy_is_complete_and_appearance_neutral(self) -> None:
        for filename in ("firefox.svg", "firefox-light.svg"):
            svg = (ROOT / "previews" / filename).read_text()
            self.assertIn(
                "Browser chrome and web surfaces carry the same semantic signal.",
                svg,
            )
            self.assertNotIn("one night palette", svg)
        for filename in ("rmux.svg", "rmux-light.svg"):
            svg = (ROOT / "previews" / filename).read_text()
            self.assertIn("34 previews verified", svg)
            self.assertIn("Dark + Light viewport pass complete", svg)
            self.assertNotIn("Viewport pass pending", svg)
            self.assertNotIn("17 previews verified", svg)

    def test_preview_styles_use_canonical_palette_roles(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("site_generate_preview", ROOT / "scripts" / "generate.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        for palette, appearance in (
            (module.load_palette(), "dark"),
            (module.load_light_palette(), "light"),
        ):
            colors = palette["colors"]
            svg = module.render_preview(module.APPS[0], palette, appearance)
            style = svg.split("<style>", 1)[1].split("</style>", 1)[0]
            expected_fills = {
                "canvas": colors["background"],
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
        dark_style = (ROOT / "previews" / "sonicterm.svg").read_text().split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertNotRegex(dark_style, r'\.dim\{fill:#928374[;}]')


    def test_readme_presents_paired_previews_and_dark_compatibility(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "![Apollo Dark for SonicTerm simulated preview](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg)",
            readme,
        )
        self.assertIn(
            "![Apollo Light for SonicTerm simulated preview](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm-light.svg)",
            readme,
        )
        self.assertIn(
            "Unsuffixed Apollo names and preview filenames remain the stable Apollo Dark compatibility surfaces",
            readme,
        )
        self.assertIn("https://apollo-theme.github.io/#ports", readme)

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
        self.assertIn('<main id="main" tabindex="-1">', html)
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

    def test_site_shows_complete_dark_and_light_palette_tables(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for palette_id, filename in (
            ("palette-dark", "apollo.json"),
            ("palette-light", "apollo-light.json"),
        ):
            self.assertEqual(html.count(f'id="{palette_id}"'), 1)
            palette = json.loads((ROOT / "palette" / filename).read_text())
            section = html.split(f'id="{palette_id}"', 1)[1].split('</article>', 1)[0]
            required = [
                palette["colors"][key]
                for key in (
                    "background", "surface", "foreground", "foregroundSecondary",
                    "foregroundInactive", "accent", "selection", "danger", "success",
                    "info", "magenta", "cyan",
                )
            ] + palette["terminal"]["ansi"] + palette["terminal"]["bright"]
            for color in required:
                self.assertIn(color, section)
            self.assertIn("Base palette", section)
            self.assertIn("ANSI", section)
            self.assertIn("Bright", section)
        self.assertIn('href="palette/apollo.json"', html)
        self.assertIn('href="palette/apollo-light.json"', html)

    def test_shell_follows_os_appearance_without_hiding_previews(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        self.assertIn('<meta name="color-scheme" content="dark light">', html)
        self.assertIn(
            '<meta name="theme-color" content="#141617" media="(prefers-color-scheme: dark)">',
            html,
        )
        self.assertIn(
            '<meta name="theme-color" content="#f9f5d7" media="(prefers-color-scheme: light)">',
            html,
        )
        self.assertIn("color-scheme:darklight", css.replace(" ", ""))
        self.assertIn("@media (prefers-color-scheme: light)", css)
        for variable in (
            "--canvas", "--surface", "--selection", "--text-primary",
            "--text-secondary", "--text-inactive", "--text-bright", "--accent",
        ):
            self.assertIn(variable, css)
        self.assertNotRegex(css, r"\.preview-(?:dark|light)\s*\{[^}]*display\s*:\s*none")


    def test_css_encodes_responsive_accessible_instrument_surface(self) -> None:
        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        for token in ("#141617", "#1d2021", "#cfbc97", "#d5c4a1", "#928374", "#fabd2f", "#3c3836"):
            self.assertIn(token, css)
        self.assertIn(":focus-visible", css)
        self.assertIn("min-height:44px", css.replace(" ", ""))
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("@media (max-width: 767px)", css)
        compact = re.sub(r"\s+", "", css)
        self.assertIn("overflow-x:hidden", compact)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("backdrop-filter", css)
        dark_root = css.split("@media (prefers-color-scheme: light)", 1)[0]
        self.assertNotIn("#665c54", dark_root)



class RepositoryContractTests(unittest.TestCase):
    def test_test_suite_is_repository_hermetic(self) -> None:
        source = (ROOT / "tests" / "test_site.py").read_text(encoding="utf-8")
        self.assertNotIn("/" + "Users/", source)

    def test_required_repository_files_and_pinned_ci_exist(self) -> None:
        required = (
            ".nojekyll", "LICENSE", "CLAUDE.md", "README.md", "index.html",
            "assets/site.css", "palette/apollo.json", "palette/apollo-light.json", "scripts/generate.py",
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
