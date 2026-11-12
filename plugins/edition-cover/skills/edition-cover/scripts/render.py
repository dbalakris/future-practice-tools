#!/usr/bin/env python3
"""Render a newsletter edition cover (1920 x 1080 PNG) from a project config.

Layout: a name tag ("Hello, my name is" and the newsletter's name) tilted on the
left of a colored ground; the edition number, title, subtitle and author on the
right; a publisher line along the bottom.

Mechanism only. Colors, fonts and every word on the cover except the title,
subtitle and number come from the project's config file (see
defaults/cover.config.json in this plugin).

Usage:
  render.py --number 1 --title "Hours saved / isn't a business strategy" \
            --subtitle "Why hours saved rarely moves business outcomes, and what to fund instead" \
            [--config path/to/edition-cover.json] [--out cover.png]

Title syntax: "/" marks the line break. **phrase** sets a phrase bold, but only
when the config has "title_bold": true; otherwise the markers are dropped.

Exit codes: 0 rendered and every check passed; 2 rendered with a failed check
(the report says which); 1 could not render.
"""
import argparse, base64, html, json, mimetypes, os, re, subprocess, sys, tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parents[2]
DEFAULT_CONFIG = PLUGIN_ROOT / "defaults" / "cover.config.json"
CONFIG_SEARCH = ["edition-cover.json", "docs/povs/edition-cover.json", ".edition-cover.json"]
FONT_CACHE = Path(os.environ.get("EDITION_COVER_FONT_CACHE", Path.home() / ".cache" / "edition-cover" / "fonts"))
W, H = 1920, 1080
PAD, GAP, TAG_W = 160, 96, 560        # side margins, badge-to-text gap, badge width


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
    t = html.escape(text or "", quote=False)
    t = re.sub(r'(^|[\s(\[])"', r'\1&ldquo;', t).replace('"', "&rdquo;")
    t = re.sub(r"(^|[\s(\[])'", r"\1&lsquo;", t).replace("'", "&rsquo;")
    return t


def lines_html(raw, allow_bold=False):
    out = []
    for line in (l.strip() for l in (raw or "").split("/")):
        esc = smart(line)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc) if allow_bold else esc.replace("**", "")
        out.append(esc)
    return "<br>".join(out)


def font_roles(cfg):
    """(family, weight, style) for every face the cover uses."""
    f = cfg["fonts"]
    roles = {}
    for role in ("title", "subtitle", "meta", "author"):
        roles[role] = (f[role]["family"], int(f[role]["weight"]), f[role].get("style", "normal"))
    roles["tag_lead"] = (f["title"]["family"], int(f["title"].get("lead_weight", 500)), "normal")
    if cfg.get("title_bold"):
        roles["title_bold"] = (f["title"]["family"], int(f["title"].get("bold_weight", 800)), "normal")
    return roles


def google_link(roles):
    fams = {}
    for fam, wt, style in roles.values():
        fams.setdefault(fam, set()).add((1 if style == "italic" else 0, wt))
    parts = []
    for fam, faces in fams.items():
        name = fam.replace(" ", "+")
        if any(i for i, _ in faces):
            parts.append(f"family={name}:ital,wght@{';'.join(f'{i},{w}' for i, w in sorted(faces))}")
        else:
            parts.append(f"family={name}:wght@{';'.join(str(w) for _, w in sorted(faces))}")
    return f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{"&".join(parts)}&display=swap">'


def local_faces(cfg, cfg_dir):
    """@font-face rules for font files named in the config (fonts.<role>.files: {weight: path})."""
    css = []
    for role in cfg["fonts"].values():
        style = role.get("style", "normal")
        for wt, rel in (role.get("files") or {}).items():
            p = (cfg_dir / rel).expanduser()
            if p.is_file():
                css.append(f'@font-face{{font-family:"{role["family"]}";font-weight:{wt};font-style:{style};src:url({data_uri(p)})}}')
    return "".join(css)


def fontsource_faces(missing):
    """Fallback when a font did not load (no network to Google Fonts): fetch the
    @fontsource npm package for each family and embed the needed faces."""
    css = []
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    for fam, wt, style in missing:
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
        f = pkg_dir / "package" / "files" / f"{slug}-latin-{wt}-{style}.woff2"
        if f.is_file():
            css.append(f'@font-face{{font-family:"{fam}";font-weight:{wt};font-style:{style};src:url({data_uri(f)}) format("woff2")}}')
        else:
            print(f"  @fontsource/{slug} has no {style} {wt}", file=sys.stderr)
    return "".join(css)


def build_html(cfg, number, title, subtitle, font_css, use_google):
    c = cfg["colors"]; f = cfg["fonts"]; t = cfg["tag"]
    def face(role):
        r = f[role]
        return f'font-family:"{r["family"]}";font-weight:{r["weight"]};font-style:{r.get("style", "normal")}'
    num = html.escape(cfg.get("number_format", "Edition {n}").format(n=number))
    author = f'<div class="by" id="by">{smart(cfg["author"])}</div>' if cfg.get("author") else ""
    footer = f'<div class="foot">{smart(cfg["footer"])}</div>' if cfg.get("footer") else ""
    tf = f["title"]
    return f"""<!doctype html><html><head><meta charset="utf-8">{google_link(font_roles(cfg)) if use_google else ""}<style>{font_css}
*{{box-sizing:border-box}}body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;position:relative;background:{c['ground']}}}
.cover{{width:{W}px;height:{H}px;display:flex;align-items:center;gap:{GAP}px;padding:0 {PAD}px}}
.tag{{width:{TAG_W}px;height:400px;flex-shrink:0;background:{c['tag']};border-radius:26px;transform:rotate(-4deg);display:flex;flex-direction:column;overflow:hidden}}
.band{{background:{c['tag_band']};color:{c['tag_band_text']};padding:22px 34px 16px;display:flex;flex-direction:column;gap:2px}}
.hello{{font-family:"{tf['family']}";font-weight:{tf['weight']};font-size:52px;line-height:1;letter-spacing:-.01em;text-transform:uppercase}}
.mni{{{face('meta')};font-size:17px;letter-spacing:.14em;text-transform:uppercase}}
.body{{flex-grow:1;display:flex;flex-direction:column;justify-content:center;padding:12px 34px 22px;gap:6px}}
.lead{{font-family:"{tf['family']}";font-weight:{tf.get('lead_weight', 500)};font-size:34px;line-height:1.05;color:{c['tag_lead']}}}
.name{{font-family:"{tf['family']}";font-weight:{tf['weight']};font-size:66px;line-height:.98;letter-spacing:-.02em;color:{c['tag_text']}}}
.strip{{height:12px;background:{c['tag_band']}}}
.col{{display:flex;flex-direction:column;gap:28px;min-width:0;flex:1}}
.no{{{face('meta')};font-size:22px;letter-spacing:.12em;text-transform:uppercase;color:{c['accent']}}}
h1{{{face('title')};margin:0;font-size:84px;line-height:1.02;letter-spacing:-.015em;color:{c['title']}}}
h1 b{{font-weight:{tf.get('bold_weight', 800)}}}
.dek{{{face('subtitle')};margin:0;font-size:34px;line-height:1.3;color:{c['subtitle']};opacity:.85;text-wrap:balance}}
.by{{{face('author')};font-size:22px;color:{c['author']};opacity:.7}}
.foot{{position:absolute;left:{PAD}px;bottom:64px;{face('meta')};font-size:20px;letter-spacing:.14em;text-transform:uppercase;color:{c['accent']}}}
</style></head><body><div class="cover">
<div class="tag" id="tag"><div class="band"><div class="hello">{smart(t['greeting'])}</div><div class="mni">{smart(t['subline'])}</div></div>
<div class="body"><div class="lead">{smart(t['lead'])}</div><div class="name" id="name">{lines_html(t['name'])}</div></div><div class="strip"></div></div>
<div class="col" id="col"><div class="no">{num}</div>
<h1 id="t">{lines_html(title, cfg.get('title_bold', False))}</h1>
<p class="dek" id="d">{smart(subtitle)}</p>{author}</div></div>
{footer}</body></html>"""


CHECK_JS = """() => {
  const t = document.getElementById('t'), d = document.getElementById('d'), tag = document.getElementById('tag'), name = document.getElementById('name');
  const by = document.getElementById('by'), col = document.getElementById('col');
  const lh = el => parseFloat(getComputedStyle(el).lineHeight);
  const r = el => el.getBoundingClientRect();
  const range = document.createRange(); range.selectNodeContents(t);
  let widest = 0; for (const rc of range.getClientRects()) widest = Math.max(widest, rc.right);
  const last = by || d;
  return {
    title_lines: Math.round(r(t).height / lh(t)),
    subtitle_lines: Math.round(r(d).height / lh(d)),
    title_right: Math.round(widest), column_right: %d,
    text_top: Math.round(r(col.firstElementChild).top), text_bottom: Math.round(r(last).bottom),
    footer_top: Math.round(r(document.querySelector('.foot') || document.body).top) - 30,
    tag_name_fits: name.scrollWidth <= name.clientWidth && tag.scrollHeight <= tag.clientHeight + 1,
  };
}""" % (W - PAD)


def render(page, doc):
    page.set_content(doc)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--number", required=True, help='edition number as it should read, e.g. "2"')
    ap.add_argument("--title", required=True, help='title; "/" marks the line break')
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--config")
    ap.add_argument("--out", help="output PNG (default: cover-<number>.png in the current folder)")
    a = ap.parse_args()

    cfg_path, is_default = find_config(a.config)
    if is_default:
        print("  no project config found; using the plugin's generic defaults", file=sys.stderr)
    cfg = load_config(cfg_path)
    out = Path(a.out or f"cover-{a.number}.png").expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is not installed. Run: pip install playwright && python -m playwright install chromium")

    roles = font_roles(cfg)
    font_css = local_faces(cfg, cfg_path.parent)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        render(page, build_html(cfg, a.number, a.title, a.subtitle, font_css, True))
        missing = [(fam, wt, st) for fam, wt, st in set(roles.values())
                   if not page.evaluate(f"[...document.fonts].some(ff => ff.family.replace(/\"/g,'') === '{fam}' && ff.style === '{st}' && String(ff.weight) === '{wt}' && ff.status === 'loaded')")]
        if missing:
            print(f"  fonts not loaded from Google Fonts: {sorted(missing)}; trying @fontsource", file=sys.stderr)
            font_css += fontsource_faces(missing)
            render(page, build_html(cfg, a.number, a.title, a.subtitle, font_css, False))
        m = page.evaluate(CHECK_JS)
        page.screenshot(path=str(out))
        browser.close()

    problems = []
    if m["title_lines"] > 2:
        problems.append(f"title runs to {m['title_lines']} lines (max 2): shorten it or move the '/' break")
    if m["title_right"] > m["column_right"]:
        problems.append("title runs past the right margin")
    if m["subtitle_lines"] > 2:
        problems.append(f"subtitle runs to {m['subtitle_lines']} lines (max 2): shorten it")
    if m["text_bottom"] > m["footer_top"] or m["text_top"] < 60:
        problems.append("the text block runs into the publisher line or off the top")
    if not m["tag_name_fits"]:
        problems.append("the name on the tag doesn't fit the tag: move its '/' break in the config")
    print(json.dumps({"out": str(out), "config": str(cfg_path), "measures": m, "problems": problems}, indent=2))
    sys.exit(2 if problems else 0)


if __name__ == "__main__":
    main()
