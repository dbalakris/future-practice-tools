# edition-cover

Makes the cover image for a newsletter edition or LinkedIn article: a 1920 x 1080 PNG with a paper sheet on a colored ground, the series name and edition number at the top, the mark at the right like a letterhead, then the title and one subtitle.

The plugin holds the layout and the renderer. Your colors, fonts, mark and series name live in your project.

## Set up your project

1. Copy `defaults/cover.config.json` to your project as `edition-cover.json` (or `docs/povs/edition-cover.json`).
2. Set `series`, the `colors`, the `fonts` (any Google Fonts family), and `mark` (a path to a transparent PNG, relative to the config file).
3. Install Playwright once: `pip install playwright && python -m playwright install chromium`.

## Use

Ask Claude for "the cover for edition 03" or "a banner for this article", with the title and subtitle. It renders the PNG, checks the title fits on two lines, and hands it back.

## Config

| Key | What it sets |
|---|---|
| `series` | The name on the series line |
| `number_format` | How the number reads, e.g. `No. {n}` |
| `title_bold` | `true` lets `**phrase**` in a title set that phrase bold |
| `mark` | Path to the mark image, relative to the config file; `null` for none |
| `colors` | `ground`, `sheet`, `sheet_edge`, `rule`, `series`, `number`, `title`, `subtitle` |
| `fonts` | `title`, `subtitle`, `series`, `number`, each a `family` and `weight`; optional `files` ({weight: path}) to use local font files instead of Google Fonts |
