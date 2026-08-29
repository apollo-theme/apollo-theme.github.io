# Apollo Theme website

The organization-root GitHub Pages site for [Apollo Theme](https://github.com/apollo-theme/apollo-theme). It presents the canonical Apollo and Apollo Light palettes across 17 permanent application ports through clearly labeled simulated interfaces.

![Apollo for SonicTerm simulated preview](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg)

## Architecture

This is a no-build static site. Browsers receive committed HTML, CSS, JSON, and SVG files with no external runtime dependencies or required JavaScript.

- `palette/apollo.json` and `palette/apollo-light.json` — exact copies of the two canonical palettes
- `scripts/generate.py` — deterministic owner of `index.html` and `previews/*.svg`
- `scripts/check.py` — complete local and CI acceptance check
- `tests/test_site.py` — executable repository contracts
- `assets/site.css` — responsive, accessible presentation that follows the OS appearance
- `previews/` — exactly 34 app-specific, social-preview-sized SVG simulations: stable dark URLs plus `-light.svg` companions

## Develop

Edit the structured app data or templates in `scripts/generate.py`, then regenerate:

```sh
python3 scripts/generate.py
```

Run the complete validation suite:

```sh
python3 scripts/check.py
```

Preview locally without any build step:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000/`. The local HTTP URL is only for development; site content links use HTTPS or local paths.

## Generated-file policy

Do not edit `index.html` or `previews/*.svg` by hand. `python3 scripts/generate.py --check` fails when committed output differs from the deterministic generator.

Every interface image is a design simulation, not a screenshot. The visible `SIMULATED PREVIEW` stamp and captions must remain in place.

## Palette lineage

Apollo is derived from Gruvbox Dark Hard through SonicTerm’s modified near-black variant; Apollo Light is an accessibility-hardened Gruvbox Light Hard variant. Their canonical lineage metadata is carried in `palette/apollo.json` and `palette/apollo-light.json`.

## License

Site code and generated assets are available under the [MIT License](LICENSE).
