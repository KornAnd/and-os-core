#!/usr/bin/env python3
"""
publish_doc.py — Publication-grade Markdown to HTML/PDF publisher.

Part of the document-hub skill (Contour: Publication, v1.1).
Reverses the ingestion pipeline: a canonical Markdown source becomes a
self-contained, print-ready HTML document (deterministic, offline, no
runtime dependencies beyond the venv: markdown-it-py + Pygments).

PDF output is opportunistic: the system HTML-to-PDF chain (cupsfilter)
is probed with a minimal document; when no filter is installed the
publisher exits 3 and the HTML artifact remains the canonical output
(print it from any browser for a pixel-identical PDF).

Mermaid fences: rendered to inline SVG when a local `mmdc` binary is
available; otherwise kept as a styled source block (SSoT = the source).

Usage:
  python3 publish_doc.py <input.md> [-o output.html|output.pdf]
                         [--title TITLE] [--author AUTHOR]
                         [--version VERSION]

Exit codes:
  0 — success (HTML written; PDF written when requested and available)
  1 — generation error
  2 — usage or missing input
  3 — PDF requested but no system HTML-to-PDF filter (HTML written)
"""

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
from datetime import date
from pathlib import Path

EXIT_OK = 0
EXIT_GEN_ERROR = 1
EXIT_USAGE = 2
EXIT_NO_PDF = 3

CODE_BLOCK_RE = re.compile(
    r'<pre><code class="language-([a-z0-9+#-]*)">(.*?)</code></pre>',
    re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$")
FENCE_RE = re.compile(r"^```")


def slugify(title: str) -> str:
    """Unicode-safe anchor slug (Latin, Cyrillic, digits, hyphens)."""
    slug = re.sub(r"[^\w-]+", "-", title.lower(), flags=re.UNICODE)
    return slug.strip("-") or "section"


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[publish_doc] ERROR: {message}\n")
    sys.stderr.write(__doc__.split("Usage:")[1].split("Exit codes:")[0])
    sys.exit(EXIT_USAGE)


def render_body(markdown_text: str) -> str:
    """Renders CommonMark+tables Markdown to HTML with Pygments code."""
    try:
        from markdown_it import MarkdownIt
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name
    except ImportError as err:
        sys.stderr.write(f"[publish_doc] ERROR: missing venv package: {err}\n")
        sys.stderr.write("Run with and_os/.venv/bin/python3\n")
        sys.exit(EXIT_GEN_ERROR)

    body = MarkdownIt("js-default").render(markdown_text)

    def pygments_match(match: re.Match) -> str:
        lang = match.group(1) or "text"
        if lang == "mermaid":
            return match.group(0)
        source = html.unescape(match.group(2))
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            lexer = get_lexer_by_name("text")
        styled = highlight(source, lexer, HtmlFormatter(noclasses=True))
        return f'<pre>{styled}</pre>'

    return CODE_BLOCK_RE.sub(pygments_match, body)


def build_toc(markdown_text: str) -> str:
    """Builds a numbered table of contents from h1/h2 headings."""
    entries = []
    in_fence = False
    for line in markdown_text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            level, title = len(match.group(1)), match.group(2).strip()
            entries.append((level, title, slugify(title)))
    if not entries:
        return ""
    items = []
    for level, title, slug in entries:
        indent = "" if level == 1 else "&nbsp;&nbsp;&nbsp;&nbsp;"
        items.append(f'<li class="toc-h{level}">{indent}'
                     f'<a href="#{slug}">{html.escape(title)}</a></li>')
    return ('<nav class="toc"><h2 class="toc-title">Contents</h2>'
            f'<ul>{"".join(items)}</ul></nav>')


def render_mermaid(block_html: str) -> str:
    """Inlines SVG for a mermaid block when a local mmdc binary exists."""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return (block_html.replace('<pre><code', '<pre class="mermaid-source"><code')
                + '<p class="mermaid-note">Mermaid source (no local '
                  'renderer detected — SSoT preserved)</p>')
    source = html.unescape(
        re.search(r'>(.*?)</code>', block_html, re.DOTALL).group(1))
    src_path = Path(os.path.join("/tmp", f"mmdc_{os.getpid()}.mmd"))
    out_path = src_path.with_suffix(".svg")
    try:
        src_path.write_text(source, encoding="utf-8")
        proc = subprocess.run([mmdc, "-i", str(src_path),
                               "-o", str(out_path)],
                              capture_output=True, text=True, timeout=120)
        if proc.returncode != 0 or not out_path.exists():
            sys.stderr.write(f"[publish_doc] WARNING: mmdc failed: "
                             f"{proc.stderr.strip()[:200]}\n")
            return block_html
        svg = out_path.read_text(encoding="utf-8")
        return (f'<figure class="mermaid-fig"><figcaption>'
                f'Diagram (mermaid)</figcaption>{svg}</figure>')
    except (OSError, subprocess.TimeoutExpired) as err:
        sys.stderr.write(f"[publish_doc] WARNING: mmdc unavailable: {err}\n")
        return block_html
    finally:
        for path in (src_path, out_path):
            if path.exists():
                path.unlink()


def finalize_mermaid(body: str) -> str:
    """Post-processes all language-mermaid code blocks."""
    def mermaid_match(match: re.Match) -> str:
        return render_mermaid(match.group(0))
    return re.sub(r'<pre><code class="language-mermaid">.*?</code></pre>',
                  mermaid_match, body, flags=re.DOTALL)


def assign_heading_ids(body: str) -> str:
    """Adds anchor ids to h1/h2 headings for TOC links."""
    counter = {}
    def heading_match(match: re.Match) -> str:
        level, inner = match.group(1), match.group(2)
        slug = slugify(inner)
        seen = counter.get(slug, 0)
        counter[slug] = seen + 1
        anchor = slug if seen == 0 else f"{slug}-{seen}"
        return f"<h{level} id=\"{anchor}\">{inner}</h{level}>"
    return re.sub(r"<h([12])>(.*?)</h\1>", heading_match, body)


PAPER_CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: Georgia, 'DejaVu Serif', serif; font-size: 11pt;
       line-height: 1.45; color: #1a1a1a; max-width: 178mm; margin: 0 auto; }
h1, h2, h3 { font-family: 'Helvetica Neue', Arial, sans-serif;
             color: #111; line-height: 1.2; }
h1 { font-size: 22pt; margin: 0 0 4mm; }
h2 { font-size: 15pt; margin-top: 8mm; border-bottom: 0.5pt solid #bbb;
     padding-bottom: 1mm; }
h3 { font-size: 12pt; margin-top: 5mm; }
p { margin: 2.2mm 0; text-align: justify; }
pre { background: #f4f4f2; border: 0.5pt solid #ddd; padding: 2.5mm;
      font-size: 8.5pt; line-height: 1.3; white-space: pre-wrap;
      print-color-adjust: exact; -webkit-print-color-adjust: exact; }
code { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 9pt; }
p code, li code, td code { background: #f0f0ee; padding: 0 1mm; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0;
        font-size: 9.5pt; }
th, td { border: 0.5pt solid #999; padding: 1.2mm 2mm; text-align: left; }
th { background: #ececea; print-color-adjust: exact;
     -webkit-print-color-adjust: exact; }
blockquote { border-left: 2pt solid #999; margin: 3mm 0; padding: 1mm 3mm;
             color: #444; }
.toc { background: #fafaf8; border: 0.5pt solid #ddd; padding: 3mm 4mm;
       margin: 5mm 0; font-size: 10pt; }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0.8mm 0; }
.toc a { color: #1a1a1a; text-decoration: none; }
.title-block { margin-bottom: 6mm; padding-bottom: 3mm;
               border-bottom: 1pt solid #333; }
.title-block h1 { margin-bottom: 2mm; }
.title-meta { font-size: 10pt; color: #555; font-family: Arial, sans-serif; }
.mermaid-note { font-size: 8pt; color: #777; font-family: Arial, sans-serif; }
h1, h2 { page-break-after: avoid; }
pre, table, figure { page-break-inside: avoid; }
"""

DOC_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<div class="title-block">
<h1>{title}</h1>
<div class="title-meta">{meta}</div>
</div>
{toc}
{body}
<div class="title-meta footer-note">Published {pub_date} &middot; v{version} &middot; document-hub</div>
</body>
</html>
"""


def detect_html_to_pdf() -> bool:
    """Probes the system for an HTML-to-PDF chain (cupsfilter filters)."""
    cupsfilter = shutil.which("cupsfilter")
    if not cupsfilter:
        return False
    probe_html = Path("/tmp") / f"pub_probe_{os.getpid()}.html"
    probe_pdf = Path("/tmp") / f"pub_probe_{os.getpid()}.pdf"
    try:
        probe_html.write_text("<html><body><p>probe</p></body></html>",
                              encoding="utf-8")
        with open(probe_pdf, "wb") as out:
            proc = subprocess.run([cupsfilter, str(probe_html)],
                                  stdout=out, stderr=subprocess.PIPE,
                                  text=True, timeout=60)
        readable = probe_pdf.read_bytes()
        return proc.returncode == 0 and readable.startswith(b"%PDF")
    except (OSError, subprocess.TimeoutExpired):
        return False
    finally:
        for path in (probe_html, probe_pdf):
            if path.exists():
                path.unlink()


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Publication md->HTML/PDF")
    parser.add_argument("input", help="Markdown source file")
    parser.add_argument("-o", "--output",
                        help="output .html or .pdf (default: <input>.html)")
    parser.add_argument("--title", help="document title (default: first H1)")
    parser.add_argument("--author", default="", help="author line")
    parser.add_argument("--version", default="1.0", help="document version")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        fail_usage(f"input markdown not found: {input_path}")
    markdown_text = input_path.read_text(encoding="utf-8")

    title = args.title
    first_lines = [l for l in markdown_text.splitlines() if l.strip()]
    if title is None and first_lines and first_lines[0].startswith("# "):
        # A leading H1 becomes the publication title (title block),
        # so it is removed from the body to avoid a double title.
        title = first_lines[0][2:].strip()
        markdown_text = markdown_text.replace(first_lines[0], "", 1)
        markdown_text = markdown_text.lstrip("\n")
    if title is None:
        title = input_path.stem
    output_path = Path(args.output) if args.output \
        else input_path.with_suffix(".html")
    want_pdf = output_path.suffix.lower() == ".pdf"
    html_path = output_path if not want_pdf \
        else output_path.with_suffix(".html")

    body = render_body(markdown_text)
    body = finalize_mermaid(body)
    body = assign_heading_ids(body)
    toc = build_toc(markdown_text)
    meta_bits = [f"Author: {args.author}"] if args.author else []
    meta_bits.append(f"Published: {date.today().isoformat()}")
    meta_bits.append(f"Version: {args.version}")

    doc = DOC_TEMPLATE.format(
        title=html.escape(title), css=PAPER_CSS,
        meta=" &middot; ".join(html.escape(b) for b in meta_bits),
        toc=toc, body=body, pub_date=date.today().isoformat(),
        version=html.escape(args.version))
    html_path.write_text(doc, encoding="utf-8")
    sys.stdout.write(f"📄 HTML written: {html_path} "
                     f"({html_path.stat().st_size} bytes)\n")
    if not want_pdf:
        return EXIT_OK

    if not detect_html_to_pdf():
        sys.stdout.write(
            f"⚠️ No system HTML-to-PDF filter found — "
            f"print {html_path} from a browser for a pixel-identical PDF.\n")
        return EXIT_NO_PDF

    cupsfilter = shutil.which("cupsfilter")
    with open(output_path, "wb") as out:
        proc = subprocess.run([cupsfilter, str(html_path)],
                              stdout=out, stderr=subprocess.PIPE,
                              text=True, timeout=300)
    if proc.returncode != 0 or not output_path.stat().st_size > 1000:
        sys.stderr.write(f"[publish_doc] ERROR: PDF conversion failed: "
                         f"{proc.stderr.strip()[:300]}\n")
        return EXIT_GEN_ERROR
    sys.stdout.write(f"📑 PDF written: {output_path} "
                     f"({output_path.stat().st_size} bytes)\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
