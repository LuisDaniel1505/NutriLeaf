"""Genera y despliega el sitio estático a la rama ``gh-pages`` de GitHub Pages.

Este script:
1. Genera el contenido estático (``index.html`` con rutas relativas, CSS, JS y el
   modelo ONNX) con codificación UTF-8 correcta.
2. Crea o actualiza la rama ``gh-pages`` y la sube a GitHub con ``git worktree``.

Uso (desde la raíz del proyecto)::

    python scripts/deploy_ghpages.py

Requiere que exista ``static/model.onnx`` (generado con ``scripts/export_onnx.py``).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANCH = "gh-pages"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un comando git desde la raíz del proyecto."""
    return subprocess.run(cmd, cwd=str(ROOT), check=check, capture_output=True, text=True)


def main() -> None:
    model = ROOT / "static" / "model.onnx"
    if not model.exists():
        raise SystemExit(
            "[error] No existe static/model.onnx. Ejecuta scripts/export_onnx.py "
            "y copia el resultado a static/."
        )

    # 1. Construir el contenido estático (UTF-8 correcto)
    tmp = Path(tempfile.mkdtemp(prefix="nutrileaf_deploy_"))
    (tmp / "css").mkdir()
    (tmp / "js").mkdir()

    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    html = html.replace("/static/", "")
    (tmp / "index.html").write_text(html, encoding="utf-8", newline="\n")

    shutil.copy2(ROOT / "static" / "css" / "style.css", tmp / "css" / "style.css")
    shutil.copy2(ROOT / "static" / "js" / "app.js", tmp / "js" / "app.js")
    shutil.copy2(model, tmp / "model.onnx")

    print(f"[info] Contenido estático generado en {tmp}")

    # 2. Desplegar a la rama gh-pages con un worktree temporal.
    wt = Path(tempfile.mkdtemp(prefix="nutrileaf_ghpages_"))
    try:
        # Si la rama ya existe (local), se elimina para recrearla limpia.
        run(["git", "branch", "-D", BRANCH], check=False)
        run(["git", "worktree", "add", "--orphan", str(wt)])
        run(["git", "-C", str(wt), "branch", "-m", BRANCH])

        for item in tmp.iterdir():
            dest = wt / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        run(["git", "-C", str(wt), "add", "-A"])
        run(["git", "-C", str(wt), "commit", "-m", "deploy: sitio estático (v1.0.0)"])
        run(["git", "push", "origin", f"{BRANCH}:{BRANCH}", "--force"])
        print("[ok] Sitio desplegado correctamente a la rama gh-pages.")
    finally:
        run(["git", "worktree", "remove", str(wt), "--force"], check=False)
        shutil.rmtree(wt, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
