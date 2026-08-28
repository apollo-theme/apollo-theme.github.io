# Apollo site contributor guide

## Scope

This repository is the no-build organization-root GitHub Pages site for Apollo Theme. Keep edits self-contained here and do not add package managers, external runtime dependencies, analytics, or trackers.

## Source of truth

- `palette/apollo.json` must remain byte-for-byte identical to the parent canonical palette.
- `scripts/generate.py` owns `index.html` and every `previews/*.svg` file.
- Run the generator after changing site content or preview data. Never hand-edit generated files.
- Keep exactly the 17 permanent `app-*` anchors and matching preview SVGs.
- Every visual presented as an app interface must remain visibly labeled `SIMULATED PREVIEW`.

## Design constraints

Preserve the Apollo night-flight console: one dark instrument surface, square rails, exact palette values, local/system monospace, and the palette-to-app signal path. Do not introduce gradients, purple, glass effects, rounded-everything, or decorative metrics. `#665c54` is ANSI bright black only and must never be normal interface text.

## Verification

Run the complete check before handing work off:

```sh
python3 scripts/check.py
```

The check validates the canonical palette hash, generated drift, semantic app inventory, SVG safety and labels, HTTPS/local URLs, contrast, documentation, and pinned Pages workflow actions.
