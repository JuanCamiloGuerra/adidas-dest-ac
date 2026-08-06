"""Genera la lectura HTML de las celdas Markdown del notebook principal."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.markdown_guide import build_markdown_guide  # noqa: E402


def main() -> None:
    notebook = ROOT / "notebooks" / "guia_integral_para_entender_proyecto_sportretail.ipynb"
    output = ROOT / "docs" / "markdown.html"
    build_markdown_guide(notebook, output)
    print(f"Guía Markdown generada: {output}")


if __name__ == "__main__":
    main()
