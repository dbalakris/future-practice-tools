#!/usr/bin/env python3
"""Render a newsletter edition cover (1920 x 1080 PNG) from a project config.

Mechanism only. Colors, fonts, the mark and the series name come from the
project's config file (see defaults/cover.config.json in this plugin).

Usage:
  render.py --number 01 --title "Hours saved isn't / a business strategy" \
            --subtitle "Why hours saved rarely moves business outcomes, and what to fund instead." \
            [--config path/to/edition-cover.json] [--out cover.png]

Title syntax: "/" marks the line break. **phrase** sets a phrase bold, but only
when the config has "title_bold": true; otherwise the markers are dropped.

Exit codes: 0 rendered and every check passed; 2 rendered with a failed check
(the report says which); 1 could not render.
"""
import argparse, base64, html, io, json, mimetypes, os, re, subprocess, sys, tarfile, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parents[2]
DEFAULT_CONFIG = PLUGIN_ROOT / "defaults" / "cover.config.json"
CONFIG_SEARCH = ["edition-cover.json", "docs/povs/edition-cover.json", ".edition-cover.json"]
FONT_CACHE = Path(os.environ.get("EDITION_COVER_FONT_CACHE", Path.home() / ".cache" / "edition-cover" / "fonts"))
W, H = 1920, 1080


def find_config(explicit):
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            sys.exit(f"Config not found: {p}")
        return p, False
    for rel in CONFIG_SEARCH:
        p = Path.cwd() / rel
        if p.is_file():
            return p, False
    return DEFAULT_CONFIG, True


def load_config(path):
    base = json.loads(DEFAULT_CONFIG.read_text())
    cfg = json.loads(Path(path).read_text())
    def merge(a, b):
        for k, v in b.items():
            a[k] = merge(a.get(k, {}), v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
        return a
    return merge(base, cfg)


def data_uri(path):
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def smart(text):
    """Escape for HTML and turn straight quotes into typographic ones."""
    t = html.escape(text, quote=False)
    t = re.sub(r'(^|[\s(\[])"', r'\1&ldquo;', t).replace('"', "&rdquo;")
    t = re.sub(r"(^|[\s(\[])'", r"\1&lsquo;", t).replace("'", "&rsquo;")
    return t


def title_html(raw, allow_bold):
    lines = [l.strip() for l in raw.split("/")]
    out = []
    for line in lines:
        esc = smart(line)
        if allow_bold:
            esc = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc)
        else:
            esc = esc.replace("**", "")
        out.append(esc)
    return "<br>".join(out)


def font_roles(cfg):
    f = cfg["fonts"]
    roles = {
        "title": (f["title"]["family"], f["title"]["weight"]),
        "subtitle": (f["subtitle"]["family"], f["subtitle"]["weight"]),
        "series": (f["series"]["family"], f["series"]["weight"]),
        "number": (f["number"]["family"], f["number"]["weight"]),
    }
    if cfg.get("title_bold"):
        roles["title_bold"] = (f["title"]["family"], f["title"].get("bold_weight", 700))
    return roles


def google_link(roles):
    fams = {}
    for fam, wt in roles.values():
        fams.setdefault(fam, set()).add(int(wt))
    parts = [f"family={fam.replace(' ', '+')}:wght@{';'.join(str(w) for w in sorted(ws))}" for fam, ws in fams.items()]
    return f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{"&".join(parts)}&display=swap">'


def local_faces(cfg, cfg_dir):
    """@font-face rules for font files named in the config (fonts.<role>.files: {weight: path})."""
    css = []
    for role in cfg["fonts"].values():
        for wt, rel in (role.get("files") or {}).items():
            p = (cfg_dir / rel).expanduser()
            if p.is_file():
                css.append(f'@font-face{{font-family:"{role["family"]}";font-weight:{wt};src:url({data_uri(p)})}}')
    return "".join(css)


def fontsource_faces(missing):
    """Fallback when a font did not load (no network to Google Fonts): fetch the
    @fontsource npm package for each family and embed the needed weights."""
    css = []
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    for fam, wt in missing:
        slug = fam.lower().replace(" ", "-")
        pkg_dir = FONT_CACHE / slug
        if not pkg_dir.exists():
            try:
                tgz = subprocess.run(["npm", "pack", f"@fontsource/{slug}", "--silent"], cwd=FONT_CACHE,
                                     capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
                with tarfile.open(FONT_CACHE / tgz) as t:
                    t.extractall(pkg_dir, filter="data")
                (FONT_CACHE / tgz).unlink(missing_ok=True)
            except Exception as e:  # noqa: BLE001
                print(f"  could not fetch @fontsource/{slug}: {e}", file=sys.stderr)
                continue
        f = pkg_dir / "package" / "files" / f"{slug}-latin-{wt}-normal.woff2"
        if f.is_file():
            css.append(f'@font-face{{font-family:"{fam}";font-weight:{wt};src:url({data_uri(f)}) format("woff2")}}')
        else:
            print(f"  @fontsource/{slug} has no weight {wt}", file=sys.stderr)
    return "".join(css)


def build_html(cfg, cfg_dir, number, title, subtitle, font_css, use_google):
    c = cfg["colors"]; f = cfg["fonts"]
    mark = ""
    if cfg.get("mark"):
        mp = (cfg_dir / cfg["mark"]).expanduser()
        if mp.is_file():
            mark = f'<img class="mark" src="{data_uri(mp)}" alt="">'
        else:
            print(f"  mark not found at {mp}; rendering without it", file=sys.stderr)
    num = html.escape(cfg.get("number_format", "No. {n}").format(n=number))
    return f"""<!doctype html><html><head><meta charset="utf-8">{google_link(font_roles(cfg)) if use_google else ""}<style>{font_css}
*{{box-sizing:border-box}}body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;position:relative;background:{c['ground']}}}
.sheet{{position:absolute;background:{c['sheet']};border:2px solid {c['sheet_edge']}}}
.back{{left:170px;top:150px;width:1610px;height:900px}}
.front{{left:140px;top:120px;width:1610px;height:900px;padding:80px 120px 0}}
.top{{display:flex;justify-content:space-between;align-items:center;min-height:40px}}
.series{{display:flex;align-items:center;gap:40px;font-family:"{f['series']['family']}";font-size:22px;font-weight:{f['series']['weight']};letter-spacing:.14em;text-transform:uppercase;color:{c['series']}}}
.no{{font-family:"{f['number']['family']}";font-weight:{f['number']['weight']};letter-spacing:.04em;text-transform:none;color:{c['number']}}}
.mark{{width:120px}}
.rule{{height:2px;background:{c['rule']};margin:32px 0 0}}
h1{{font-family:"{f['title']['family']}";font-size:96px;line-height:1.08;font-weight:{f['title']['weight']};margin:190px 0 0;letter-spacing:-.01em;color:{c['title']}}}
h1 b{{font-weight:{f['title'].get('bold_weight', 700)}}}
.dek{{font-family:"{f['subtitle']['family']}";font-weight:{f['subtitle']['weight']};font-size:30px;line-height:1.3;margin:36px 0 0;color:{c['subtitle']};max-width:1100px}}
</style></head><body>
<div class="sheet back"></div>
<div class="sheet front" id="front">
<div class="top"><div class="series"><span>{html.escape(cfg['series'])}</span><span class="no">{num}</span></div>{mark}</div>
<div class="rule"></div>
<h1 id="t">{title_html(title, cfg.get('title_bold', False))}</h1>
<p class="dek" id="d">{smart(subtitle)}</p>
</div></body></html>"""


CHECK_JS = """() => {
  const t = document.getElementById('t'), d = document.getElementById('d'), s = document.getElementById('front');
  const lh = el => parseFloat(getComputedStyle(el).lineHeight);
  const r = el => el.getBoundingClientRect();
  const inner = r(s).right - 120;
  const range = document.createRange(); range.selectNodeContents(t);
  let widest = 0; for (const rc of range.getClientRects()) widest = Math.max(widest, rc.right);
  return {
    title_lines: Math.round(r(t).height / lh(t)),
    subtitle_lines: Math.round(r(d).height / lh(d)),
    title_right: Math.round(widest), sheet_inner_right: Math.round(inner),
    text_bottom: Math.round(r(d).bottom), sheet_bottom: Math.round(r(s).bottom) - 60,
  };
}"""


def render(page, doc):
    page.set_content(doc)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--number", required=True, help='edition number as it should read, e.g. "01"')
    ap.add_argument("--title", required=True, help='title; "/" marks the line break')
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--config")
    ap.add_argument("--out", help="output PNG (default: cover-<number>.png in the current folder)")
    a = ap.parse_args()

    cfg_path, is_default = find_config(a.config)
    if is_default:
        print("  no project config found; using the plugin's generic defaults", file=sys.stderr)
    cfg = load_config(cfg_path)
    cfg_dir = cfg_path.parent
    out = Path(a.out or f"cover-{a.number}.png").expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is not installed. Run: pip install playwright && python -m playwright install chromium")

    roles = font_roles(cfg)
    font_css = local_faces(cfg, cfg_dir)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        render(page, build_html(cfg, cfg_dir, a.number, a.title, a.subtitle, font_css, True))
        missing = [(fam, wt) for fam, wt in set(roles.values())
                   if not page.evaluate(f"document.fonts.check('{wt} 40px \"{fam}\"')")
                   or not page.evaluate(f"[...document.fonts].some(ff => ff.family.replace(/\"/g,'') === '{fam}' && ff.status === 'loaded')")]
        if missing:
            print(f"  fonts not loaded from Google Fonts: {sorted(missing)}; trying @fontsource", file=sys.stderr)
            font_css += fontsource_faces(missing)
            render(page, build_html(cfg, cfg_dir, a.number, a.title, a.subtitle, font_css, False))
        m = page.evaluate(CHECK_JS)
        page.screenshot(path=str(out))
        browser.close()

    problems = []
    if m["title_lines"] > 2:
        problems.append(f"title runs to {m['title_lines']} lines (max 2): shorten it or move the '/' break")
    if m["title_right"] > m["sheet_inner_right"]:
        problems.append("title runs past the sheet's right margin")
    if m["subtitle_lines"] > 2:
        problems.append(f"subtitle runs to {m['subtitle_lines']} lines (max 2): shorten it")
    if m["text_bottom"] > m["sheet_bottom"]:
        problems.append("text runs off the bottom of the sheet")
    print(json.dumps({"out": str(out), "config": str(cfg_path), "measures": m, "problems": problems}, indent=2))
    sys.exit(2 if problems else 0)


if __name__ == "__main__":
    main()
