# edition-cover

Makes the cover image for a newsletter edition or LinkedIn article: a 1920 x 1080 PNG with a "Hello, my name is" name tag carrying the newsletter's name on the left, the edition number, title, subtitle and author on the right, and a publisher line along the bottom.

The plugin holds the layout and the renderer. Your colors, fonts and the words on the cover live in your project.

## Set up your project

1. Copy `defaults/cover.config.json` to your project as `edition-cover.json` (or `docs/povs/edition-cover.json`).
2. Set the `tag` wording, `author`, `footer`, the `colors` and the `fonts` (any Google Fonts family).
3. Install Playwright once: `pip install playwright && python -m playwright install chromium`.

## Use

Ask Claude for "the cover for edition 03" or "a banner for this article", with the title and subtitle. It renders the PNG, checks the title fits on two lines, and hands it back.

## Config

| Key | What it sets |
|---|---|
| `number_format` | How the number reads, e.g. `Edition {n}` |
| `title_bold` | `true` lets `**phrase**` in a title set that phrase bold |
| `tag` | `greeting` ("Hello"), `subline` ("My name is"), `lead` ("The") and `name`, the newsletter's name; `/` in `name` marks its line break |
| `author` | The byline under the subtitle; empty for none |
| `footer` | The publisher line at the bottom; empty for none |
| `colors` | `ground`, `tag`, `tag_band`, `tag_band_text`, `tag_text`, `title`, `subtitle`, `meta` (number, author, footer) |
| `fonts` | `title` (also the tag; `lead_weight` for "The"), `subtitle` (`style: italic` allowed), `meta`, `author`; each a `family` and `weight`, optional `files` ({weight: path}) for local font files |

Upgrading from 1.0.0: `series`, `mark`, and the `sheet`, `sheet_edge`, `rule`, `series` and `number` colors are gone. Copy the new keys from `defaults/cover.config.json`.
