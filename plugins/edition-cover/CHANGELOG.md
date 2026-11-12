# Changelog

## 2.1.0 (2026-11-12)

Matches the owner's canvas board (`BadgeCover.dc.html`) exactly: badge 560 x 400, rounded 26px, tilted -4°; the badge and the text column centered side by side; title 84px; subtitle 34px; gold accent on the edition number and publisher line. Config colors: `meta` is replaced by `accent`, and `tag_lead` ("The") and `author` are new.

## 2.0.0 (2026-11-12)

The cover is now the name tag: a tilted "Hello, my name is" tag with the newsletter's name on the left, edition number, title, subtitle and author on the right, publisher line at the bottom, matching the edition 1 cover. Replaces the 1.0.0 letterhead layout, which was wrong. Config changes (breaking): new `tag`, `author`, `footer` keys and tag colors; `series`, `mark` and the sheet colors are removed. The subtitle font can be italic. New check: the newsletter's name fits on the tag.

## 1.0.0 (2026-11-10)

First release. One skill, `edition-cover`, with the letterhead layout: paper sheet on a colored ground, series line and mark at the top, title on up to two lines, one subtitle. Checks title and subtitle length. Loads fonts from Google Fonts and falls back to @fontsource when Google Fonts can't be reached.
