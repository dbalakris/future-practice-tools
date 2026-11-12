# Eval cases

Run each; the expected result is what the skill should do, not just what the script returns.

| # | Input | Expected |
|---|---|---|
| 1 | Edition 1, "Hours saved isn't a business strategy", subtitle "Why hours saved rarely moves business outcomes, and what to fund instead." | Breaks after "isn't"; exit 0; mentions the subtitle repeats "hours saved" and offers one alternative without changing it |
| 2 | Title of 14+ words | Exit 2 on title lines; skill moves the break once, then asks the user to shorten; never reduces the font size |
| 3 | Subtitle of 40+ words | Exit 2 on subtitle lines; skill asks for a shorter subtitle |
| 4 | Run from a folder with no edition-cover.json | Renders with generic defaults; skill says so and offers to set up a config |
| 5 | User asks for "a banner for this article" with a `docs/povs/<slug>/` folder | Reads the title from pov.md, asks for number and subtitle only, writes `docs/povs/<slug>/cover.png` |
| 6 | Title with an apostrophe or ampersand | Renders the curly apostrophe and the ampersand correctly |
| 7 | Edition 2, "What AI Strategy?", subtitle "Four questions to get "Define our AI strategy" off your to-do list" | One-line title; the name tag on the left reads "The AI Native Operator"; reads as the same cover as edition 1 |
