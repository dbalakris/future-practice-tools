---
name: edition-cover
description: Make the cover image (1920 x 1080 PNG) for a newsletter edition or LinkedIn article — the "banner" at the top of the piece — from its number, title and subtitle, in the project's own colors, fonts and mark. Use when asked for a cover, title card or article banner for an edition.
---

# Edition cover

Renders one cover: a paper sheet on a colored ground, the series name and edition number at the top with the mark at the right like a letterhead, then the title and one subtitle. Layout lives here; colors, fonts, mark and series name live in the project's `edition-cover.json`.

## Steps

1. **Get the three inputs.** Edition number, title, subtitle. If the user gave a draft folder (`docs/povs/<slug>/`), read the title from its `pov.md` and ask only for what is missing. Use the title exactly as written: never retitle, never "improve" it.
2. **Place the line break.** Two lines at most. Break where the title has a natural pause, keeping a phrase together ("Hours saved isn't / a business strategy"). Mark it with `/`.
3. **Render.** From the project root:
   `python3 <this skill's folder>/scripts/render.py --number 01 --title "..." --subtitle "..." --out <path>`
   Default output: `docs/povs/<slug>/cover.png` when a slug folder exists, else ask. The script finds `edition-cover.json` or `docs/povs/edition-cover.json` itself; pass `--config` otherwise. No config found means generic defaults: say so and offer to set one up from `defaults/cover.config.json`.
4. **Read the report.** Exit 2 lists what failed (title over two lines, past the margin, subtitle too long). Fix by moving the break, or ask the user to shorten. Never shrink the type.
5. **Look at it** before handing it over, then send the PNG with one line: what it says and that it is ready to upload as the article's cover image.

Checks and the reasons behind the layout: `references/definition-of-good.md`. Setup problems (Playwright, fonts): the script prints the fix.
