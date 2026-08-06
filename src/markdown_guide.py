"""Publica las celdas Markdown de la guía integral como una página legible.

Entradas: notebook principal del proyecto.
Salida: HTML autónomo con la narrativa metodológica y enlace al código completo.
Dependencias: biblioteca estándar.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from src.site_navigation import navigation_css, navigation_html


def _inline(text: str) -> str:
    """Convierte el formato inline más frecuente sin ejecutar HTML del notebook."""

    value = html.escape(text)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    return value


def _render_markdown(source: str) -> str:
    """Renderiza títulos, listas, párrafos, citas y bloques de código."""

    blocks: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    in_code = False
    code: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            blocks.append(f"</{list_kind}>")
            list_kind = None

    for raw in source.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        item = re.match(r"^\s*([-*]|\d+\.)\s+(.+)$", line)
        if item:
            flush_paragraph()
            kind = "ol" if item.group(1)[0].isdigit() else "ul"
            if list_kind != kind:
                close_list()
                blocks.append(f"<{kind}>")
                list_kind = kind
            blocks.append(f"<li>{_inline(item.group(2))}</li>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_list()
            blocks.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
            continue
        paragraph.append(line.strip())

    flush_paragraph()
    close_list()
    if code:
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
    return "".join(blocks)


def build_markdown_guide(notebook_path: Path, output_path: Path) -> None:
    """Crea una lectura web continua de la explicación contenida en el notebook."""

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = [
        _render_markdown("".join(cell.get("source", [])))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "markdown" and cell.get("source")
    ]
    content = "".join(f'<section class="chapter">{cell}</section>' for cell in cells)
    document = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Guía Markdown | SportRetail LAM</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#efefec;color:#111;font-family:Arial,sans-serif;line-height:1.65}}
.hero{{background:#000;color:#fff;padding:72px max(24px,calc((100vw - 1040px)/2)) 58px}}
.hero span{{color:#d7ff3f;font-size:10px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}}
.hero h1{{font-size:clamp(48px,8vw,100px);line-height:.85;letter-spacing:-.07em;text-transform:uppercase;margin:18px 0}}
.hero p{{color:#d5d5d5;max-width:780px;font-size:18px}}.hero a{{display:inline-block;background:#d7ff3f;color:#000;padding:13px 18px;text-decoration:none;font-weight:900;text-transform:uppercase;font-size:10px}}
main{{max-width:1040px;margin:auto;padding:30px 22px 80px}}.chapter{{background:#fff;color:#111;border:1px solid #aaa;border-top:5px solid #000;padding:30px;margin:14px 0}}
h1,h2,h3,h4{{line-height:1.05;letter-spacing:-.035em}}h1{{font-size:42px}}h2{{font-size:34px;border-bottom:2px solid #111;padding-bottom:10px}}h3{{font-size:24px}}p,li{{color:#292929}}code{{background:#ececec;color:#111;padding:2px 5px}}pre{{background:#111;color:#f4f4f4;padding:18px;overflow:auto}}pre code{{background:transparent;color:inherit;padding:0}}blockquote{{margin:18px 0;background:#efffc0;color:#111;border-left:7px solid #000;padding:15px 18px}}a{{color:#153fb5}}
{navigation_css()}</style></head><body>{navigation_html("markdown")}
<header class="hero"><span>Fase 2 · Guía narrativa</span><h1>El proyecto,<br>paso a paso.</h1><p>Lectura continua de las explicaciones del notebook principal. El código, las salidas ejecutadas y las tablas completas permanecen en el archivo reproducible.</p><a href="https://github.com/JuanCamiloGuerra/adidas-dest-ac/blob/main/notebooks/guia_integral_para_entender_proyecto_sportretail.ipynb">Abrir notebook completo →</a></header>
<main>{content}</main></body></html>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
