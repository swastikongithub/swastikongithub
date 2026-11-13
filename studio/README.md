# studio

The generator for the images on the profile. Each one is a weave rendered thread by thread.

```sh
cd studio
npm install                       # Libre Caslon (SIL Open Font License)
pip install -r requirements.txt
python build.py                   # writes ../assets/*-light.svg and *-dark.svg
```

| File | Purpose |
|---|---|
| `loom.py` | Drafts (threading, tie-up, treadling), their drawdown, basic structures, and the float renderer |
| `typeset.py` | Shapes text with HarfBuzz and writes it as SVG outlines, since images in a README can't load fonts |
| `build.py` | The five plates and the two themes |

## Rules the plates follow

- **Width.** Every plate is 1048 units wide (262 warp ends at a pitch of 4) and is shown at full README width.
- **Colour.** There are two inks per theme, warp and weft. Madder appears only where something is being pointed out: the beater as the masthead is woven, the step-through in the draft, the stripe boundaries, and one stripe of the tartan. The README chooses the theme with `<picture>` and `prefers-color-scheme`.
- **Narrow screens.** Each SVG responds to its own rendered width. Below 560 px the small labels hide and larger ones take their place.
- **Motion.** The masthead is woven once, about 2.4 s, and the draft steps through its product. Both are removed under `prefers-reduced-motion`. The still frame is complete, and so is the frame a renderer without CSS animation would show.
- **GitHub.** There is no script, no external reference and no web font. Styles are inline in each SVG, which GitHub serves as an image.

The language shares in `COMPOSITION` were measured on 13 Nov 2026 as non-blank lines of code per language across seven public repositories, excluding docs, migrations, lockfiles, and minified or vendored files. Update them by hand when they drift.
