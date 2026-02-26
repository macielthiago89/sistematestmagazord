
from __future__ import annotations

import io
import os
import re
import sys
import json
import time
import shutil
import zipfile
import textwrap
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_file, send_from_directory, abort

from env_check import run_checks

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
ASSETS_DIR = STATIC_DIR / "assets"

DATA_DIR = (APP_DIR / "data").resolve()
PROJECT_DIR = DATA_DIR / "TesteMagazord"   # extracted zip content lives here
RUNS_DIR = STATIC_DIR / "runs"
PDF_CACHE_DIR = DATA_DIR / "_pdf_cache"
FONTS_DIR = ASSETS_DIR / "fonts"

TAGS = [
    "regression",
    "APIMAGAZORD",
    "E2EMAGAZORD",
    "FRONTENDMAGAZORD",
    "ARQUIVOSMAGAZORD",
    "MOBILEMAGAZORD",
    "PIRAMIDEMAGAZORD",
    "MOCKSMAGAZORD",
]


ALLOWED_RUN_FILES = [
  "parte1-api/questao1.1/tests/1.1test.robot",
  "parte1-api/questao1.1/tests/1.2test.robot",
  "parte2-2e2/questao2.1/2.1test.robot",
  "parte2-2e2/questao2.2/2.2test.robot",
  "parte3-frontend/questao3.1/tests/3.1test.robot",
  "parte4-arquivos/questao4.1/tests/4.1test.robot",
  "parte5-mobile/questao5.1/testes/5.1test.robot.robot",
  "parte6-piramide/questao6.1/tests/6.1test.robot",
  "parte6-piramide/questao6.1/tests/6.2test.robot",
  "parte7-mocks/questao7.1/tests/7.1test.robot"
]

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

# ----------------------------
# Helpers
# ----------------------------

def _safe_rel(path: str) -> Path:
    """
    Accepts a relative path from the frontend and ensures it can't escape PROJECT_DIR.
    """
    p = Path(path).as_posix().lstrip("/")
    full = (PROJECT_DIR / p).resolve()
    if PROJECT_DIR not in full.parents and full != PROJECT_DIR:
        raise ValueError("Invalid path")
    return full

def _norm_rel(rel: str) -> str:
    return str(rel).replace('\\\\','/').lstrip('/')


def _ensure_extracted() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    if PROJECT_DIR.exists() and any(PROJECT_DIR.iterdir()):
        return

    # Extract embedded zip (app/static/assets/magazord.zip) into PROJECT_DIR
    zip_path = ASSETS_DIR / "magazord.zip"
    if not zip_path.exists():
        raise RuntimeError(f"Missing asset zip: {zip_path}")

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(PROJECT_DIR)

    # Ensure a Unicode-capable font for PDF generation (fixes "squares" in README)
    try:
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
        for fp in candidates:
            if fp.exists():
                shutil.copy(fp, FONTS_DIR / fp.name)
    except Exception:
        pass

def _list_dir_tree(rel: str) -> Dict[str, Any]:
    base = _safe_rel(rel)
    if not base.exists():
        raise FileNotFoundError(rel)

    items = []
    for p in sorted(base.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if p.name in {"__pycache__", ".git"}:
            continue
        items.append({
            "name": p.name,
            "is_dir": p.is_dir(),
            "rel": str(p.relative_to(PROJECT_DIR)).replace("\\", "/"),
        })
    return {"path": rel, "items": items}

def _find_suites(base: Path) -> List[Path]:
    """
    Determine what to execute under a selected folder.
    Prefer 'tests' directory if present and contains .robot files.
    Otherwise run any .robot under the folder.
    """
    suites: List[Path] = []
    tests_dir = base / "tests"
    if tests_dir.exists():
        robot_files = list(tests_dir.rglob("*.robot"))
        if robot_files:
            suites.append(tests_dir)
            return suites

    # else, if any .robot in base
    if list(base.rglob("*.robot")):
        suites.append(base)
    return suites

def _tail_text(s: str, max_chars: int = 4000) -> str:
    if len(s) <= max_chars:
        return s
    return "...\n" + s[-max_chars:]

def _slug(s: str) -> str:
    s = s.replace("\\", "/")
    s = re.sub(r"[^a-zA-Z0-9/_-]+", "_", s).strip("_")
    s = s.replace("/", "__")
    return s[:120] or "suite"

# ----------------------------
# Markdown -> PDF (simple)
# ----------------------------

def _md_to_plain(md: str) -> str:
    # Remove code fences but keep content, remove md syntax lightly
    md = re.sub(r"```.*?\n", "", md)
    md = md.replace("```", "")
    md = re.sub(r"^#{1,6}\s*", "", md, flags=re.MULTILINE)
    md = re.sub(r"!\[.*?\]\(.*?\)", "", md)
    md = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", md)
    md = re.sub(r"[*_]{1,3}", "", md)
    return md.strip()

def _plain_to_pdf_bytes(title: str, text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 48
    top = height - 56
    line_h = 14

    # Register a font that supports UTF-8 accents/symbols.
    try:
        regular = FONTS_DIR / "DejaVuSans.ttf"
        bold = FONTS_DIR / "DejaVuSans-Bold.ttf"
        if regular.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(regular)))
        if bold.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(bold)))
        title_font = "DejaVuSans-Bold" if bold.exists() else "DejaVuSans"
        body_font = "DejaVuSans" if regular.exists() else "Helvetica"
    except Exception:
        title_font = "Helvetica-Bold"
        body_font = "Helvetica"

    c.setFont(title_font, 14)
    c.drawString(left, top, title)
    y = top - 24

    c.setFont(body_font, 10)

    def _sanitize_for_pdf(s: str) -> str:
        """ReportLab/TTF won't render emoji; keep common Latin text and punctuation."""
        if not s:
            return ""
        # Replace common bullets/dashes first
        s = s.replace("•", "-")
        s = s.replace("–", "-")
        s = s.replace("—", "-")
        # Drop characters outside BMP that are frequently emoji/symbols
        s = "".join(ch for ch in s if ord(ch) <= 0xFFFF)
        # Remove other pictographic symbols (best-effort)
        s = re.sub(r"[\U0001F300-\U0001FAFF]", "", s)
        return s

    for para in text.splitlines():
        para = _sanitize_for_pdf(para)
        if not para.strip():
            y -= line_h
            continue
        wrapped = textwrap.wrap(para, width=105)
        for line in wrapped:
            if y < 60:
                c.showPage()
                c.setFont(body_font, 10)
                y = height - 56
            c.drawString(left, y, line)
            y -= line_h

    c.showPage()
    c.save()
    return buffer.getvalue()

def _md_file_to_pdf(path: Path) -> Path:
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _slug(str(path.relative_to(PROJECT_DIR)))
    out = PDF_CACHE_DIR / f"{key}.pdf"

    # simple cache: re-generate if source is newer
    if out.exists() and out.stat().st_mtime >= path.stat().st_mtime:
        return out

    md = path.read_text(encoding="utf-8", errors="ignore")
    plain = _md_to_plain(md)
    pdf_bytes = _plain_to_pdf_bytes(path.name, plain)
    out.write_bytes(pdf_bytes)
    return out

# ----------------------------
# API
# ----------------------------

@app.get("/")
def index():
    _ensure_extracted()
    resp = send_from_directory(str(STATIC_DIR), "index.html")
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@app.get("/api/tags")
def api_tags():
    return jsonify({"tags": TAGS})

@app.get("/api/roots")
def api_roots():
    _ensure_extracted()
    roots = []
    for p in sorted(PROJECT_DIR.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name.startswith("parte"):
            roots.append({"name": p.name, "rel": p.name})
    # also include readme + requirements at top
    extras = []
    for name in ["readme.md", "requirements.txt", "lista_arquivos.txt"]:
        fp = PROJECT_DIR / name
        if fp.exists():
            extras.append({"name": name, "rel": name})
    return jsonify({"roots": roots, "extras": extras})

@app.get("/api/tree")
def api_tree():
    _ensure_extracted()
    rel = request.args.get("path", "").strip() or "."
    try:
        data = _list_dir_tree(rel if rel != "." else "")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/theory")
def api_theory():
    _ensure_extracted()
    items = []
    # include root readme
    root_readme = PROJECT_DIR / "readme.md"
    if root_readme.exists():
        items.append({"title": "README", "rel": "readme.md"})

    # find all RESPOSTA_TEORICA.md (title should be friendly, without full path)
    for p in sorted(PROJECT_DIR.rglob("RESPOSTA_TEORICA.md"), key=lambda x: str(x).lower()):
        rel = str(p.relative_to(PROJECT_DIR)).replace("\\", "/")
        parent = p.parent
        # Example: parte3-frontend/questao3.1
        title = str(parent.relative_to(PROJECT_DIR)).replace("\\", "/")
        items.append({"title": title, "rel": rel})

    return jsonify({"items": items})

@app.get("/api/md")
def api_md():
    _ensure_extracted()
    rel = request.args.get("path", "").strip()
    if not rel:
        return jsonify({"error": "path required"}), 400
    try:
        p = _safe_rel(rel)
        if not p.exists() or p.is_dir():
            return jsonify({"error": "file not found"}), 404
        txt = p.read_text(encoding="utf-8", errors="ignore")
        return jsonify({"path": rel, "content": txt})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/pdf")
def api_pdf():
    _ensure_extracted()
    rel = request.args.get("path", "").strip()
    download = (request.args.get("download") or "").strip() == "1"
    if not rel:
        abort(400)
    try:
        p = _safe_rel(rel)
        if not p.exists() or p.is_dir():
            abort(404)
        out = _md_file_to_pdf(p)
        return send_file(str(out), mimetype="application/pdf", as_attachment=download, download_name=out.name)
    except Exception:
        abort(400)


@app.get("/api/has_robot")
def api_has_robot():
    """
    Frontend uses this to enable/disable the "Executar" button.

    Requirement (per delivery spec):
    - Only enable execution for a fixed allow-list of suite files.
    """
    _ensure_extracted()
    rel = (request.args.get("path") or "").strip()
    if not rel:
        return jsonify({"has_robot": False})

    reln = _norm_rel(rel)

    # Only files in allow-list are runnable
    if reln in ALLOWED_RUN_FILES:
        try:
            p = _safe_rel(reln)
            return jsonify({"has_robot": p.exists() and p.is_file()})
        except Exception:
            return jsonify({"has_robot": False})

    return jsonify({"has_robot": False})





@app.post("/api/install_requirements")
def api_install_requirements():
    """Install PROJECT_DIR/requirements.txt into the current Python environment."""
    _ensure_extracted()
    req = PROJECT_DIR / "requirements.txt"
    if not req.exists():
        return jsonify({"ok": False, "error": "requirements.txt não encontrado no projeto."}), 404

    # Run pip in a subprocess so we can capture output for preview
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    try:
        p = subprocess.run(cmd, cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60*20)
        out = (p.stdout or "") + ("\n" + (p.stderr or "") if p.stderr else "")
        return jsonify({"ok": p.returncode == 0, "returncode": p.returncode, "output": _tail_text(out, 12000)})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Timeout ao instalar requirements (20 min)."}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def _which(cmd: str) -> Optional[str]:
    from shutil import which
    return which(cmd)


def _parse_requirements(req_text: str) -> List[str]:
    pkgs: List[str] = []
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # ignore editable / VCS / local paths
        if line.startswith(("-e ", "git+", "http:", "https:", "./", "../")):
            continue
        # strip markers
        line = line.split(";")[0].strip()
        # package name ends before version specifiers
        name = re.split(r"[<=>~!\[]", line, maxsplit=1)[0].strip()
        if name:
            pkgs.append(name)
    return sorted(set(pkgs), key=str.lower)


@app.get("/api/check")
def api_check():
    """
    Verifica se o ambiente está pronto para executar os testes.
    Retorna o que está OK e o que está fora de conformidade.
    """
    _ensure_extracted()
    req = PROJECT_DIR / "requirements.txt"
    data = run_checks(str(PROJECT_DIR), str(req))
    return jsonify(data)



@app.post("/api/clear_runs")
def api_clear_runs():
    """
    Clears recent executions (static/runs). Frontend uses this for the 'Limpar' button.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    for p in RUNS_DIR.iterdir():
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
        elif p.is_file():
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
    return jsonify({"ok": True, "removed": removed})

@app.post("/api/run")
def api_run():
    _ensure_extracted()
    body = request.get_json(force=True, silent=True) or {}
    rel = (body.get("path") or "").strip()
    tag = (body.get("tag") or "").strip()
    tag = re.sub(r"\s+", "", tag)


    reln = _norm_rel(rel)
    # Only suites in allow-list are runnable
    if reln not in ALLOWED_RUN_FILES:
        return jsonify({"error": "selection is not runnable (allowed suites only)"}), 400
    rel = reln

    if not rel:
        return jsonify({"error": "path required"}), 400
    if tag not in TAGS:
        return jsonify({"error": "invalid tag"}), 400

    # Target can be a folder OR a single .robot file
    try:
        target = _safe_rel(rel)
        if not target.exists():
            return jsonify({"error": "target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    suites: List[Path] = []
    if target.is_file() and target.suffix.lower() == ".robot":
        suites = [target]
    elif target.is_dir():
        suites = _find_suites(target)

    if not suites:
        return jsonify({"error": "no .robot suites found in this selection"}), 400

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + _slug(rel)
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build robot command
    # -d: output dir
    # --log / --report: names (avoid collisions)
    cmd = ["robot", "-i", tag, "-d", str(out_dir), "--log", "log.html", "--report", "report.html"]
    for s in suites:
        cmd.append(str(s))

    # Execute
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
        shell=False,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    result = {
        "run_id": run_id,
        "returncode": proc.returncode,
        "cmd": cmd,
        "stdout_tail": _tail_text(stdout),
        "stderr_tail": _tail_text(stderr),
        "log_url": f"/static/runs/{run_id}/log.html" if (out_dir / "log.html").exists() else None,
        "report_url": f"/static/runs/{run_id}/report.html" if (out_dir / "report.html").exists() else None,
        "output_xml_url": f"/static/runs/{run_id}/output.xml" if (out_dir / "output.xml").exists() else None,
    }
    # save console logs
    (out_dir / "console_stdout.txt").write_text(stdout, encoding="utf-8", errors="ignore")
    (out_dir / "console_stderr.txt").write_text(stderr, encoding="utf-8", errors="ignore")

    # persist metadata for /api/runs
    try:
        meta = {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "returncode": proc.returncode,
            "cmd": cmd,
            "target": rel,
            "tag": tag,
        }
        (out_dir / "result.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return jsonify(result)

@app.get("/api/runs")
def api_runs():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = []
    for p in sorted(RUNS_DIR.iterdir(), key=lambda x: x.name, reverse=True):
        if not p.is_dir():
            continue
        runs.append({
            "run_id": p.name,
            "created_at": None,
            "returncode": None,
            "has_log": (p / "log.html").exists(),
            "has_report": (p / "report.html").exists(),
            "log_url": f"/static/runs/{p.name}/log.html" if (p / "log.html").exists() else None,
            "report_url": f"/static/runs/{p.name}/report.html" if (p / "report.html").exists() else None,
            "stdout_url": f"/static/runs/{p.name}/console_stdout.txt" if (p / "console_stdout.txt").exists() else None,
            "stderr_url": f"/static/runs/{p.name}/console_stderr.txt" if (p / "console_stderr.txt").exists() else None,
        })

        # try load result.json
        meta_path = p / "result.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8", errors="ignore"))
                runs[-1]["created_at"] = meta.get("created_at")
                runs[-1]["returncode"] = meta.get("returncode")
                runs[-1]["tag"] = meta.get("tag")
                runs[-1]["target"] = meta.get("target")
            except Exception:
                pass
    return jsonify({"runs": runs})

@app.get("/api/open_zip")
def api_open_zip():
    """
    Optional: user can drop a new zip path (local), server extracts it replacing PROJECT_DIR.
    Frontend can call this with ?path=C:\\... (useful when running locally).
    """
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "path required"}), 400
    zp = Path(path)
    if not zp.exists() or zp.suffix.lower() != ".zip":
        return jsonify({"error": "zip not found"}), 404

    # Replace
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR, ignore_errors=True)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp, "r") as zf:
        zf.extractall(PROJECT_DIR)
    return jsonify({"ok": True})

def open_browser(url: str) -> None:
    import webbrowser
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    _ensure_extracted()
    host = os.environ.get("MAGAZORD_HOST", "127.0.0.1")
    port = int(os.environ.get("MAGAZORD_PORT", "8765"))

    url = f"http://{host}:{port}/"
    if os.environ.get("MAGAZORD_NO_BROWSER") != "1":
        threading.Timer(0.8, open_browser, args=(url,)).start()

    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()
