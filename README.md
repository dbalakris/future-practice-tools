# Future Practice tools

Tools from [Future Practice Studio](https://github.com/dbalakris), packaged as Claude Code plugins. This repo is a plugin marketplace: add it once, then install the tools you want.

A tool holds the mechanism and generic defaults. Your own settings, client lists and results live in your project, never in the tool. You install a tool rather than copying it, so you get fixes when you choose to upgrade.

## Add the marketplace

```bash
claude plugin marketplace add dbalakris/future-practice-tools
```

## Install a tool

```bash
claude plugin install prospector@future-practice-tools
claude plugin install edition-cover@future-practice-tools
```

## Tools

| Tool | What it does | Status |
|---|---|---|
| prospector | Finds companies whose recent events make them live prospects, from your own triggers, and routes results where you say | 0.0.1 placeholder; 1.0.0 in progress |
| edition-cover | Makes the cover image for a newsletter edition or LinkedIn article from its number, title and subtitle, in your own colors, fonts and mark | 1.0.0 |

## Layout

```
.claude-plugin/marketplace.json   the catalog
plugins/<tool>/                   one folder per tool
  .claude-plugin/plugin.json      name and version
  skills/  defaults/  references/ mechanism and generic starting values
  README.md  CHANGELOG.md
```
