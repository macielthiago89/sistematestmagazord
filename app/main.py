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
import socket
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_file, send_from_directory, abort, Response

from env_check import run_checks

def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))

def _python_cmd_prefix() -> List[str]:
    """Return a command prefix to run Python modules in a subprocess.

    In a PyInstaller .exe, sys.executable points to the EXE, so we must use a real
    Python interpreter (env var MAGAZORD_PYTHON_EXE, or py launcher, or python in PATH).
    """
    exe = os.environ.get("MAGAZORD_PYTHON_EXE")
    if exe and Path(exe).exists():
        return [exe]

    # Prefer Windows py launcher if available
    from shutil import which
    if which("py"):
        # try to pick installed default (3.x)
        return ["py", "-3"]
    if which("python"):
        return ["python"]
    # Last resort: when running from source, sys.executable is fine
    return [sys.executable]


def _subprocess_creationflags() -> int:
    """Avoid flashing a console window when packaged with --noconsole."""
    if _is_frozen() and os.name == "nt":
        try:
            return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        except Exception:
            return 0
    return 0

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
ASSETS_DIR = STATIC_DIR / "assets"

DATA_DIR = (APP_DIR / "data").resolve()
PROJECT_DIR = DATA_DIR / "TesteMagazord"   # conteúdo do zip extraído fica aqui
RUNS_DIR = STATIC_DIR / "runs"
PDF_CACHE_DIR = DATA_DIR / "_pdf_cache"
FONTS_DIR = ASSETS_DIR / "fonts"

def _norm_tag(t: str) -> str:
    return re.sub(r"\s+", "", (t or "")).strip().lower()


# Tags mostradas na interface e aceitas na execução.
# Mantemos tudo em minúsculas para evitar inconsistência e porque os arquivos
# .robot podem declarar tags em maiúsculas/minúsculas.
TAGS = [
    "regression",
    "apimagazord",
    "e2emagazord",
    "frontendmagazord",
    "arquivosmagazord",
    "mobilemagazord",
    "piramidemagazord",
    "mocksmagazord",
]

# Tags disponíveis para seleção manual na interface.
# A tag "regression" será executada via botão dedicado (executa tudo).
UI_TAGS = [t for t in TAGS if t != "regression"]


def _extract_robot_tags_from_file(p: Path) -> List[str]:
    """Melhor esforço para extrair tags de um único arquivo .robot."""
    try:
        raw = p.read_bytes()
    except Exception:
        return []

    text = None
    for enc in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            pass
    if text is None:
        try:
            text = raw.decode("latin-1")
        except Exception:
            return []

    tags: List[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("[tags]"):
            rest = s[len("[tags]"):].strip()
            parts = re.split(r"\s{2,}|\t+", rest)
            for t in parts:
                t = t.strip()
                if t:
                    tags.append(t)

    # Normaliza para facilitar comparação (e evita duplicatas com diferentes caixas)
    out: List[str] = []
    seen = set()
    for t in tags:
        nt = _norm_tag(t)
        if not nt:
            continue
        if nt not in seen:
            seen.add(nt)
            out.append(nt)
    return out


ALLOWED_RUN_FILES = [
  "parte1-api/questao1.1/tests/1.1test.robot",
  "parte1-api/questao1.1/tests/1.2test.robot",
  "parte2-e2e/questao2.1/2.1test.robot",
  "parte2-e2e/questao2.2/2.2test.robot",
  "parte3-frontend/questao3.1/tests/3.1test.robot",
  "parte4-arquivos/questao4.1/tests/4.1test.robot",
  "parte5-mobile/questao5.1/testes/5.1test.robot.robot",
  "parte6-piramide/questao6.1/tests/6.1test.robot",
  "parte6-piramide/questao6.1/tests/6.2test.robot",
  "parte7-mocks/questao7.1/tests/7.1test.robot"
]

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")

# ----------------------------
# Shutdown/keepalive helpers (portable EXE)
# ----------------------------
_LAST_ALIVE_TS = time.time()
_SHUTDOWN_DEADLINE: float | None = None
_SHUTDOWN_LOCK = threading.Lock()

def _touch_alive() -> None:
    global _LAST_ALIVE_TS, _SHUTDOWN_DEADLINE
    _LAST_ALIVE_TS = time.time()
    # cancel any pending shutdown
    _SHUTDOWN_DEADLINE = None

def _schedule_shutdown(delay_sec: float = 2.5) -> None:
    global _SHUTDOWN_DEADLINE
    with _SHUTDOWN_LOCK:
        _SHUTDOWN_DEADLINE = time.time() + max(0.5, float(delay_sec))

def _shutdown_watcher() -> None:
    # background thread: exits process when shutdown was requested and no new alive pings arrived
    while True:
        time.sleep(0.4)
        with _SHUTDOWN_LOCK:
            deadline = _SHUTDOWN_DEADLINE
        if not deadline:
            # Safety net for packaged EXE: if the UI disappears and no heartbeat arrives
            # for a while, terminate to avoid the process getting stuck in Task Manager.
            # (Only applies to frozen builds; during dev you may keep the server running.)
            if _is_frozen() and (time.time() - _LAST_ALIVE_TS) > 35:
                os._exit(0)
            continue
        now = time.time()
        # If reached deadline and no recent activity, exit.
        if now >= deadline and (now - _LAST_ALIVE_TS) > 1.2:
            os._exit(0)

        # Extra safety: even if shutdown was never requested, exit if no alive ping arrives.
        if _is_frozen() and (now - _LAST_ALIVE_TS) > 35:
            os._exit(0)

@app.get("/api/is_frozen", endpoint="mag_is_frozen")
def api_is_frozen():
    return jsonify({"frozen": bool(getattr(sys, "frozen", False))})

# Guard against double registration (can happen in some packaging/launcher scenarios)
if "mag_alive" not in app.view_functions:
    @app.post("/api/alive", endpoint="mag_alive")
    def api_alive():
        _touch_alive()
        return jsonify({"ok": True, "ts": _LAST_ALIVE_TS})

if "mag_shutdown" not in app.view_functions:
    @app.post("/api/shutdown", endpoint="mag_shutdown")
    def api_shutdown():
        # request graceful shutdown after a short delay (allows page reloads to cancel via /api/alive)
        _schedule_shutdown(2.5)
        return jsonify({"ok": True})
# ----------------------------
# Funções Auxiliares
# ----------------------------

def _safe_rel(path: str) -> Path:
    """
    Aceita um caminho relativo do frontend e garante que não escape do PROJECT_DIR.
    """
    p = Path(path).as_posix().lstrip("/")
    full = (PROJECT_DIR / p).resolve()
    if PROJECT_DIR not in full.parents and full != PROJECT_DIR:
        raise ValueError("Caminho inválido")
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

    # Extrai o zip incorporado (app/static/assets/magazord.zip) para PROJECT_DIR
    zip_path = ASSETS_DIR / "magazord.zip"
    if not zip_path.exists():
        raise RuntimeError(f"Arquivo zip não encontrado: {zip_path}")

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(PROJECT_DIR)

    # Garante uma fonte compatível com Unicode para geração de PDF (corrige "quadrados" no README)
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
    Determina o que executar em uma pasta selecionada.
    Prefere o diretório 'tests' se presente e contiver arquivos .robot.
    Caso contrário, executa qualquer .robot na pasta.
    """
    suites: List[Path] = []
    tests_dir = base / "tests"
    if tests_dir.exists():
        robot_files = list(tests_dir.rglob("*.robot"))
        if robot_files:
            suites.append(tests_dir)
            return suites

    # senão, se houver algum .robot em base
    if list(base.rglob("*.robot")):
        suites.append(base)
    return suites

def _tail_text(s: str, max_chars: int = 4000) -> str:
    if len(s) <= max_chars:
        return s
    return "...\n" + s[-max_chars:]


def _decode_bytes(b: bytes) -> str:
    if b is None:
        return ""
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return b.decode(enc, errors="replace")
        except Exception:
            continue
    try:
        return b.decode(errors="replace")
    except Exception:
        return repr(b)

def _run_cmd(cmd, cwd=None, timeout=None):
    p = subprocess.run(
        cmd,
        cwd=cwd,
        timeout=timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        creationflags=_subprocess_creationflags(),
    )

    # Decodifica sem causar erro no Windows
    stdout = (p.stdout or b"").decode("utf-8", errors="replace")
    stderr = (p.stderr or b"").decode("utf-8", errors="replace")

    return p.returncode, stdout, stderr



def _iter_process_lines(cmd: List[str], cwd: str):
    """Produz linhas de saída de um processo em execução (mesclando stdout+stderr), decodificadas com segurança."""
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
        shell=False,
        creationflags=_subprocess_creationflags(),
    )
    try:
        assert p.stdout is not None
        for raw in iter(p.stdout.readline, b""):
            if not raw:
                break
            yield _decode_bytes(raw).rstrip("\r\n")
    finally:
        try:
            if p.stdout:
                p.stdout.close()
        except Exception:
            pass
    rc = p.wait()
    return rc
def _slug(s: str) -> str:
    s = s.replace("\\", "/")
    s = re.sub(r"[^a-zA-Z0-9/_-]+", "_", s).strip("_")
    s = s.replace("/", "__")
    return s[:120] or "suite"

# ----------------------------
# Markdown -> PDF (simples)
# ----------------------------

def _md_to_plain(md: str) -> str:
    # Remove blocos de código mas mantém o conteúdo, remove sintaxe markdown levemente
    md = re.sub(r"```.*?\n", "", md)
    md = md.replace("```", "")
    md = re.sub(r"^#{1,6}\s*", "", md, flags=re.MULTILINE)
    md = re.sub(r"!\[.*?\]\(.*?\)", "", md)
    md = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", md)
    md = re.sub(r"[*_]{1,3}", "", md)
    return md.strip()


def _read_text_auto(path: Path) -> str:
    """Lê texto com detecção de BOM/UTF-16 (comum no Windows).

    Alguns arquivos .md fornecidos (notadamente readme.md) podem ser salvos como UTF-16 e
    aparecerão como "quadrados" se lidos como UTF-8. Esta função auxiliar mantém prévias
    e PDFs legíveis em todos os ambientes.
    """
    raw = path.read_bytes()
    if not raw:
        return ""

    # Verificação de BOM
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        try:
            return raw.decode("utf-16")
        except Exception:
            pass

    # Heurística: muitos bytes NUL => provavelmente UTF-16LE/BE sem BOM
    sample = raw[:512]
    nul_ratio = sample.count(b"\x00") / max(1, len(sample))
    if nul_ratio > 0.10:
        for enc in ("utf-16", "utf-16le", "utf-16be"):
            try:
                return raw.decode(enc)
            except Exception:
                continue

    return raw.decode("utf-8", errors="replace")

def _plain_to_pdf_bytes(title: str, text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 48
    right = 48
    top = height - 56
    line_h = 14

    # Registra uma fonte que suporte acentos/símbolos UTF-8.
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

    body_size = 10
    c.setFont(body_font, body_size)

    max_w = (width - left - right)

    def _string_w(s: str) -> float:
        try:
            return pdfmetrics.stringWidth(s, body_font, body_size)
        except Exception:
            # fallback: assume monospace-ish width
            return float(len(s) * 5.5)

    def _wrap_to_width(s: str) -> List[str]:
        """Wrap text to available PDF width using real font metrics.

        This avoids lines being visually "cut" when long words/URLs exceed the page width.
        """
        if not s:
            return [""]

        # Preserve indentation (useful for pseudo-code / bullets)
        indent = re.match(r"^\s+", s)
        indent_str = indent.group(0) if indent else ""
        core = s[len(indent_str):]

        words = core.split(" ")
        lines: List[str] = []
        cur = ""

        def flush() -> None:
            nonlocal cur
            if cur != "":
                lines.append(indent_str + cur)
                cur = ""

        for w in words:
            if w == "":
                # multiple spaces -> treat as one (PDF)
                continue

            candidate = (cur + " " + w).strip() if cur else w
            if _string_w(indent_str + candidate) <= max_w:
                cur = candidate
                continue

            # current line is full
            flush()

            # word itself may be too long; break it
            if _string_w(indent_str + w) <= max_w:
                cur = w
                continue

            chunk = ""
            for ch in w:
                cand2 = chunk + ch
                if _string_w(indent_str + cand2) <= max_w:
                    chunk = cand2
                else:
                    if chunk:
                        lines.append(indent_str + chunk)
                    chunk = ch
            if chunk:
                # start next line with leftover chunk
                cur = chunk

        flush()
        return lines if lines else [indent_str]

    def _sanitize_for_pdf(s: str) -> str:
        """ReportLab/TTF não renderiza emoji; mantém texto latino comum e pontuação."""
        if not s:
            return ""
        # Substitui marcadores comuns primeiro
        s = s.replace("•", "-")
        s = s.replace("–", "-")
        s = s.replace("—", "-")
        # Remove caracteres fora do BMP que são frequentemente emoji/símbolos
        s = "".join(ch for ch in s if ord(ch) <= 0xFFFF)
        # Remove outros símbolos pictográficos (melhor esforço)
        s = re.sub(r"[\U0001F300-\U0001FAFF]", "", s)
        return s

    for para in text.splitlines():
        para = _sanitize_for_pdf(para)
        if not para.strip():
            y -= line_h
            continue
        wrapped = _wrap_to_width(para)
        for line in wrapped:
            if y < 60:
                c.showPage()
                c.setFont(body_font, body_size)
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

    # cache simples: regenera se a fonte for mais recente.
    # Em build (PyInstaller), __file__ pode apontar para um caminho interno que não existe
    # como arquivo no disco; então não dependemos do mtime do gerador.
    try:
        generator_mtime = Path(__file__).stat().st_mtime
    except Exception:
        generator_mtime = 0.0
    src_mtime = max(path.stat().st_mtime, generator_mtime)
    if out.exists() and out.stat().st_mtime >= src_mtime:
        return out

    md = _read_text_auto(path)
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
    return jsonify({"tags": UI_TAGS})


@app.get("/favicon.ico")
def favicon():
    # Silencia erros 404 no console do navegador.
    return ("", 204)

@app.get("/api/roots")
def api_roots():
    _ensure_extracted()
    roots = []
    for p in sorted(PROJECT_DIR.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name.startswith("parte"):
            roots.append({"name": p.name, "rel": p.name})
    # também inclui readme + requirements no nível superior
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

    # inclui readme raiz
    root_readme = PROJECT_DIR / "readme.md"
    if root_readme.exists():
        items.append({"title": "README", "rel": "readme.md"})

    # inclui explicacao do sistema (raiz)
    explain_md = PROJECT_DIR / "explicacaodosistema.md"
    if explain_md.exists():
        items.append({"title": "Explicação do Sistema", "rel": "explicacaodosistema.md"})

    # encontra todos os arquivos RESPOSTA_TEORICA.md (título amigável, sem caminho completo)
    for p in sorted(PROJECT_DIR.rglob("RESPOSTA_TEORICA.md"), key=lambda x: str(x).lower()):
        rel = str(p.relative_to(PROJECT_DIR)).replace("\\", "/")
        parent = p.parent
        # Exemplo: parte3-frontend/questao3.1
        title = str(parent.relative_to(PROJECT_DIR)).replace("\\", "/")
        items.append({"title": title, "rel": rel})

    return jsonify({"items": items})

@app.get("/api/md")
def api_md():
    _ensure_extracted()
    rel = request.args.get("path", "").strip()
    if not rel:
        return jsonify({"error": "caminho necessário"}), 400
    try:
        p = _safe_rel(rel)
        if not p.exists() or p.is_dir():
            return jsonify({"error": "arquivo não encontrado"}), 404
        txt = _read_text_auto(p)
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
    except Exception as e:
        # Evita "Bad Request" genérico no frontend e facilita diagnóstico pós-build
        # (ex.: reportlab não incluído no build / dependência ausente).
        return jsonify({"error": "Falha ao gerar PDF", "detail": str(e)}), 500


@app.get("/api/has_robot")
def api_has_robot():
    """
    O frontend usa isso para habilitar/desabilitar o botão "Executar".

    Requisito (conforme especificação da entrega):
    - Habilita execução apenas para uma lista fixa de arquivos de suíte.
    """
    _ensure_extracted()
    rel = (request.args.get("path") or "").strip()
    if not rel:
        return jsonify({"has_robot": False})

    reln = _norm_rel(rel)

    # Apenas arquivos na lista de permitidos são executáveis
    if reln in ALLOWED_RUN_FILES:
        try:
            p = _safe_rel(reln)
            return jsonify({"has_robot": p.exists() and p.is_file()})
        except Exception:
            return jsonify({"has_robot": False})

    return jsonify({"has_robot": False})

@app.post("/api/install_requirements")
def api_install_requirements():
    """Instala PROJECT_DIR/requirements.txt no ambiente Python atual."""
    _ensure_extracted()
    req = PROJECT_DIR / "requirements.txt"
    if not req.exists():
        return jsonify({"ok": False, "error": "requirements.txt não encontrado no projeto."}), 404

    cmd = _python_cmd_prefix() + ["-m", "pip", "install", "-r", str(req)]
    try:
        rc, stdout, stderr = _run_cmd(cmd, cwd=str(PROJECT_DIR), timeout=60 * 20)

        # Junta saída com segurança
        out_parts = []
        if stdout:
            out_parts.append(stdout)
        if stderr:
            out_parts.append(stderr)
        out = "\n".join(out_parts)

        tail = _tail_text(out, 12000)
        if rc == 0:
            tail = (tail + "\n\n✅ Instalação concluída. Agora clique em 'Verificar ambiente' para revalidar.").strip()
        else:
            tail = (tail + "\n\n⚠️ Instalação terminou com erro. Veja acima os detalhes.").strip()

        return jsonify({"ok": rc == 0, "returncode": rc, "output": tail})

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Tempo limite excedido ao instalar requirements (20 min)."}), 500
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
        # ignora pacotes editáveis / VCS / caminhos locais
        if line.startswith(("-e ", "git+", "http:", "https:", "./", "../")):
            continue
        # remove marcadores
        line = line.split(";")[0].strip()
        # nome do pacote termina antes dos especificadores de versão
        name = re.split(r"[<=>~!\[]", line, maxsplit=1)[0].strip()
        if name:
            pkgs.append(name)
    return sorted(set(pkgs), key=str.lower)


@app.post("/api/install_requirements_stream")
def api_install_requirements_stream():
    """
    Transmite a saída do pip install em tempo real (para que a interface mostre o progresso).
    """
    _ensure_extracted()
    req = PROJECT_DIR / "requirements.txt"
    if not req.exists():
        return jsonify({"ok": False, "error": "requirements.txt não encontrado em TesteMagazord."}), 404

    cmd = _python_cmd_prefix() + ["-m", "pip", "install", "-r", str(req)]

    def generate():
        yield "Iniciando instalação...\n"
        yield f"Comando: {' '.join(cmd)}\n\n"

        rc = 1
        lines: List[str] = []
        try:
            p = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                shell=False,
            creationflags=_subprocess_creationflags(),
    )
            assert p.stdout is not None
            for raw in iter(p.stdout.readline, b""):
                if not raw:
                    break
                line = _decode_bytes(raw).rstrip("\r\n")
                lines.append(line)
                if len(lines) > 3000:
                    lines = lines[-1800:]
                yield line + "\n"
            try:
                p.stdout.close()
            except Exception:
                pass
            rc = p.wait()
        except Exception as e:
            yield f"\n❌ Erro: {e}\n"
            rc = 1

        # Opcional: persiste a última saída para depuração
        try:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            (RUNS_DIR / "_last_install.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", errors="ignore")
        except Exception:
            pass

        yield f"\n__END__=ok:{'true' if rc==0 else 'false'} rc:{rc}\n"

    return Response(generate(), mimetype="text/plain; charset=utf-8")


@app.get("/api/check")
def api_check():
    """
    Verifica se o ambiente está pronto para executar os testes.
    Retorna o que está OK e o que está em não conformidade.
    """
    _ensure_extracted()
    req = PROJECT_DIR / "requirements.txt"
    data = run_checks(str(PROJECT_DIR), str(req), python_cmd=_python_cmd_prefix())
    return jsonify(data)


def _count_regression_suites() -> int:
    """Melhor esforço para contar suítes provavelmente executadas pela execução regression-all."""
    _ensure_extracted()
    count = 0
    skip_dirs = {".git", "__pycache__", "logs", "None", "_pdf_cache"}
    for p in PROJECT_DIR.rglob("*.robot"):
        rel = str(p.relative_to(PROJECT_DIR)).replace("\\", "/")
        if any(seg in skip_dirs for seg in p.parts):
            continue
        # conta apenas suítes nas pastas tests/testes
        if "/tests/" in rel or "/testes/" in rel:
            count += 1
    return count


@app.get("/api/regression_count")
def api_regression_count():
    """Retorna quantas suítes serão alvo da ação 'regression all'."""
    try:
        n = _count_regression_suites()
        return jsonify({"count": n})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)}), 200



@app.post("/api/clear_runs")
def api_clear_runs():
    """
    Limpa execuções recentes (static/runs). O frontend usa isso para o botão 'Limpar'.
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


@app.get("/api/robot_tags")
def api_robot_tags():
    """Retorna tags detectadas em um arquivo .robot (melhor esforço)."""
    _ensure_extracted()
    rel = (request.args.get("path") or "").strip()
    if not rel:
        return jsonify({"error": "caminho necessário"}), 400
    reln = _norm_rel(rel)
    try:
        target = _safe_rel(reln)
        if not target.exists() or not target.is_file():
            return jsonify({"error": "alvo não encontrado"}), 404
        if target.suffix.lower() != ".robot":
            return jsonify({"error": "não é um arquivo .robot"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    tags = _extract_robot_tags_from_file(target)
    return jsonify({"ok": True, "tags": tags})

@app.post("/api/run")
def api_run():
    _ensure_extracted()
    body = request.get_json(force=True, silent=True) or {}
    rel = (body.get("path") or "").strip()
    tag = _norm_tag(body.get("tag") or "")


    reln = _norm_rel(rel)
    # Apenas suítes na lista de permitidos são executáveis
    if reln not in ALLOWED_RUN_FILES:
        return jsonify({"error": "seleção não é executável (apenas suítes permitidas)"}), 400
    rel = reln

    if not rel:
        return jsonify({"error": "caminho necessário"}), 400
    if tag not in TAGS:
        return jsonify({"error": "tag inválida"}), 400

    # Alvo pode ser uma pasta OU um único arquivo .robot
    try:
        target = _safe_rel(rel)
        if not target.exists():
            return jsonify({"error": "alvo não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    suites: List[Path] = []
    if target.is_file() and target.suffix.lower() == ".robot":
        suites = [target]
    elif target.is_dir():
        suites = _find_suites(target)

    if not suites:
        return jsonify({"error": "nenhuma suíte .robot encontrada nesta seleção"}), 400

    # Valida se a tag está presente na suíte selecionada (executamos seleções de arquivo único neste app)
    # Isso evita erros confusos de "nenhum teste correspondente à tag".
    suite_tags = _extract_robot_tags_from_file(suites[0]) if suites and suites[0].is_file() else []
    # Regra do desafio: só executa se a tag estiver no arquivo selecionado.
    # Se não conseguirmos detectar tags, também bloqueia (evita falsa execução).
    if (not suite_tags) or (tag not in suite_tags):
        return jsonify({
            "error": "tag_not_found_in_suite",
            "message": "A tag selecionada não está presente neste arquivo de teste.",
            "available_tags": suite_tags,
        }), 400

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + _slug(rel)
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Comando robot
    # -d: diretório de saída
    # --log / --report: nomes (evita colisões)
    # Usa "python -m robot" para evitar problemas de PATH no Windows.
    cmd = _python_cmd_prefix() + ["-m", "robot", "-i", tag, "-d", str(out_dir), "--log", "log.html", "--report", "report.html"]
    for s in suites:
        cmd.append(str(s))

    # Executa
    try:
        rc, stdout, stderr = _run_cmd(cmd, cwd=str(PROJECT_DIR))
    except Exception as e:
        return jsonify({"error": "execução_falhou", "message": str(e), "cmd": cmd}), 500

    result = {
        "run_id": run_id,
        "returncode": rc,
        "cmd": cmd,
        "stdout_tail": _tail_text(stdout),
        "stderr_tail": _tail_text(stderr),
        "log_url": f"/static/runs/{run_id}/log.html" if (out_dir / "log.html").exists() else None,
        "report_url": f"/static/runs/{run_id}/report.html" if (out_dir / "report.html").exists() else None,
        "output_xml_url": f"/static/runs/{run_id}/output.xml" if (out_dir / "output.xml").exists() else None,
    }
    # salva logs do console
    (out_dir / "console_stdout.txt").write_text(stdout, encoding="utf-8", errors="ignore")
    (out_dir / "console_stderr.txt").write_text(stderr, encoding="utf-8", errors="ignore")

    # persiste metadados para /api/runs
    try:
        meta = {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "returncode": rc,
            "cmd": cmd,
            "target": rel,
            "tag": tag,
        }
        (out_dir / "result.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return jsonify(result)


@app.post("/api/run_regression_all")
def api_run_regression_all():
    """Executa todas as suítes em PROJECT_DIR filtrando pela tag 'regression'."""
    _ensure_extracted()

    tag = "regression"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + "REGRESSION_ALL"
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Executa a partir da raiz do projeto, para que o Robot descubra sub-suítes.
    # Usa "python -m robot" para evitar problemas de PATH no Windows.
    cmd = _python_cmd_prefix() + ["-m", "robot", "-i", tag, "-d", str(out_dir), "--log", "log.html", "--report", "report.html", str(PROJECT_DIR)]

    try:
        rc, stdout, stderr = _run_cmd(cmd, cwd=str(PROJECT_DIR))
    except Exception as e:
        return jsonify({"error": "execução_falhou", "message": str(e), "cmd": cmd}), 500

    result = {
        "run_id": run_id,
        "returncode": rc,
        "cmd": cmd,
        "stdout_tail": _tail_text(stdout),
        "stderr_tail": _tail_text(stderr),
        "log_url": f"/static/runs/{run_id}/log.html" if (out_dir / "log.html").exists() else None,
        "report_url": f"/static/runs/{run_id}/report.html" if (out_dir / "report.html").exists() else None,
        "output_xml_url": f"/static/runs/{run_id}/output.xml" if (out_dir / "output.xml").exists() else None,
    }

    (out_dir / "console_stdout.txt").write_text(stdout, encoding="utf-8", errors="ignore")
    (out_dir / "console_stderr.txt").write_text(stderr, encoding="utf-8", errors="ignore")

    try:
        meta = {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "returncode": rc,
            "cmd": cmd,
            "target": ".",
            "tag": tag,
            "mode": "regression_all",
        }
        (out_dir / "result.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return jsonify(result)


@app.post("/api/run_regression_all_stream")
def api_run_regression_all_stream():
    """
    Transmite a saída da execução do robot para a ação 'regression all' em tempo real.
    Envia linhas para o cliente em tempo real e emite uma linha JSON __META__ no final.
    """
    _ensure_extracted()

    tag = "regression"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + "REGRESSION_ALL"
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = _python_cmd_prefix() + ["-m", "robot", "-i", tag, "-d", str(out_dir), "--log", "log.html", "--report", "report.html", str(PROJECT_DIR)]

    def generate():
        yield f"RUN_ID: {run_id}\n"
        yield f"Comando: {' '.join(cmd)}\n\n"
        rc = 1
        stdout_lines: List[str] = []
        try:
            # Transmite e também mantém um tail seguro na memória
            p = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                shell=False,
            creationflags=_subprocess_creationflags(),
    )
            assert p.stdout is not None
            for raw in iter(p.stdout.readline, b""):
                if not raw:
                    break
                line = _decode_bytes(raw).rstrip("\r\n")
                stdout_lines.append(line)
                if len(stdout_lines) > 2000:
                    stdout_lines = stdout_lines[-1200:]
                yield line + "\n"
            try:
                p.stdout.close()
            except Exception:
                pass
            rc = p.wait()
        except Exception as e:
            yield f"\n❌ Erro: {e}\n"
            rc = 1

        # Persiste saída do console
        try:
            (out_dir / "console_stdout.txt").write_text("\n".join(stdout_lines) + "\n", encoding="utf-8", errors="ignore")
        except Exception:
            pass

        meta = {
            "run_id": run_id,
            "returncode": rc,
            "cmd": cmd,
            "log_url": f"/static/runs/{run_id}/log.html" if (out_dir / "log.html").exists() else None,
            "report_url": f"/static/runs/{run_id}/report.html" if (out_dir / "report.html").exists() else None,
            "output_xml_url": f"/static/runs/{run_id}/output.xml" if (out_dir / "output.xml").exists() else None,
        }
        yield "\n__META__=" + json.dumps(meta, ensure_ascii=False) + "\n"
        yield f"\n__END__=ok:{'true' if rc==0 else 'false'} rc:{rc}\n"

    return Response(generate(), mimetype="text/plain; charset=utf-8")

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

        # tenta carregar result.json
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
    Opcional: usuário pode fornecer um novo caminho de zip (local), o servidor extrai substituindo PROJECT_DIR.
    O frontend pode chamar isso com ?path=C:\\... (útil ao executar localmente).
    """
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "caminho necessário"}), 400
    zp = Path(path)
    if not zp.exists() or zp.suffix.lower() != ".zip":
        return jsonify({"error": "zip não encontrado"}), 404

    # Substitui
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR, ignore_errors=True)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp, "r") as zf:
        zf.extractall(PROJECT_DIR)
    return jsonify({"ok": True})

def open_browser(url: str) -> None:
    """Open the UI.

    When packaged as an EXE, opening a normal browser tab is not enough: closing a
    *tab* doesn't close the browser process, so our EXE can keep running forever.

    For frozen builds on Windows, we try to launch Edge/Chrome in "app" mode (a
    dedicated window/process). When that window closes, we terminate the EXE.
    """

    # Prefer explicit browser path if provided
    browser_exe = (os.environ.get("MAGAZORD_BROWSER_EXE") or "").strip().strip('"')

    def _start_app_window(exe: str, kind: str) -> Optional[subprocess.Popen]:
        try:
            tmp_root = (DATA_DIR / "_browser_profile").resolve()
            tmp_root.mkdir(parents=True, exist_ok=True)
            # isolate profile so the window is its own process and exits when closed
            profile = tmp_root / f"{kind}_{int(time.time())}"
            profile.mkdir(parents=True, exist_ok=True)
            args = [
                exe,
                f"--app={url}",
                "--new-window",
                "--no-first-run",
                "--disable-extensions",
                f"--user-data-dir={str(profile)}",
            ]
            return subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=_subprocess_creationflags(),
            )
        except Exception:
            return None

    # When frozen, prefer app-mode window so we can terminate reliably.
    if _is_frozen() and os.name == "nt":
        from shutil import which

        cand: List[Tuple[str, str]] = []
        if browser_exe and Path(browser_exe).exists():
            cand.append((browser_exe, "custom"))

        for exe, kind in (("msedge", "edge"), ("chrome", "chrome"), ("chromium", "chromium")):
            p = which(exe)
            if p:
                cand.append((p, kind))

        # also check common install paths (Edge often not on PATH)
        common_paths = [
            (os.environ.get("ProgramFiles(x86)", "") + r"\\Microsoft\\Edge\\Application\\msedge.exe", "edge"),
            (os.environ.get("ProgramFiles", "") + r"\\Microsoft\\Edge\\Application\\msedge.exe", "edge"),
            (os.environ.get("ProgramFiles(x86)", "") + r"\\Google\\Chrome\\Application\\chrome.exe", "chrome"),
            (os.environ.get("ProgramFiles", "") + r"\\Google\\Chrome\\Application\\chrome.exe", "chrome"),
        ]
        for pth, kind in common_paths:
            if pth and Path(pth).exists():
                cand.append((pth, kind))

        proc: Optional[subprocess.Popen] = None
        for exe, kind in cand:
            proc = _start_app_window(exe, kind)
            if proc is not None:
                break

        if proc is not None:
            def _wait_and_exit() -> None:
                try:
                    proc.wait()
                except Exception:
                    pass
                # give the shutdown watcher a nudge, then exit hard
                try:
                    _schedule_shutdown(0.5)
                except Exception:
                    pass
                time.sleep(0.6)
                os._exit(0)

            threading.Thread(target=_wait_and_exit, daemon=True).start()
            return

    # Fallback: normal browser tab
    import webbrowser
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _pick_free_port(host: str, preferred: int) -> int:
    # try preferred; if unavailable, bind to port 0 to get a free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, int(preferred)))
            return int(preferred)
        except OSError:
            s.bind((host, 0))
            return int(s.getsockname()[1])
    finally:
        try:
            s.close()
        except Exception:
            pass


def main():
    _ensure_extracted()
    host = os.environ.get("MAGAZORD_HOST", "127.0.0.1")
    port = int(os.environ.get("MAGAZORD_PORT", "8765"))

    # Start a daemon watcher so the EXE can terminate after the UI tab closes.
    # The frontend calls /api/shutdown on pagehide; /api/alive cancels it while the UI is open.
    threading.Thread(target=_shutdown_watcher, daemon=True).start()

    url = f"http://{host}:{port}/"
    if os.environ.get("MAGAZORD_NO_BROWSER") != "1":
        t = threading.Timer(0.8, open_browser, args=(url,))
        # Important: timer threads are non-daemon by default; make it daemon so it never keeps the EXE alive.
        t.daemon = True
        t.start()

    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()