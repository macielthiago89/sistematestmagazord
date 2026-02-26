from __future__ import annotations

import os
import re
import sys
import json
import platform
import importlib
import importlib.metadata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from shutil import which

def _which(cmd: str) -> Optional[str]:
    return which(cmd)

def _parse_requirements(req_text: str) -> List[str]:
    pkgs: List[str] = []
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-e ", "git+", "http:", "https:", "./", "../")):
            continue
        line = line.split(";")[0].strip()
        name = re.split(r"[<=>~!\[]", line, maxsplit=1)[0].strip()
        if name:
            pkgs.append(name)
    return sorted(set(pkgs), key=str.lower)

def _import_ok(pkg: str) -> bool:
    # mapeamento de melhor esforço entre nome pip e nome de importação
    mapping = {
        "robotframework": "robot",
        # nome pip -> nome de importação
        "Faker": "faker",
        "Pillow": "PIL",
        "pywin32": "win32api",
        "python-dotenv": "dotenv",
        "google-auth-oauthlib": "google_auth_oauthlib",
        "google-auth": "google.auth",
        "robotframework-databaselibrary": "DatabaseLibrary",
        "robotframework-faker": "FakerLibrary",
        "robotframework-retryfailed": "RetryFailed",
        "robotframework-sikulilibrary": "SikuliLibrary",
        "robotframework-requests": "RequestsLibrary",
        "robotframework-seleniumlibrary": "SeleniumLibrary",
    }
    mod = mapping.get(pkg, pkg)
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def _dist_ok(pkg: str) -> bool:
    """Retorna True se a distribuição pip parece instalada (mesmo se a importação falhar)."""
    # A consulta de metadados não diferencia maiúsculas/minúsculas e normaliza '-'/'_' internamente.
    try:
        importlib.metadata.version(pkg)
        return True
    except Exception:
        return False

def run_checks(project_dir: str, requirements_path: str, python_cmd: list[str] | None = None) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_exe": (python_cmd[0] if python_cmd else sys.executable),
        "robot_cmd": _which("robot"),
        "pip_cmd": _which("pip"),
        "node_cmd": _which("node"),
        "npm_cmd": _which("npm"),
        "adb_cmd": _which("adb"),
        "ok": True,
        "problems": [],
        "packages_missing": [],
        "packages_ok": [],
        "packages_installed_but_import_failed": [],
    }

    # verificação do módulo Python robot
    try:
        import robot  # type: ignore
        info["robot_module"] = getattr(robot, "__version__", "ok")
    except Exception:
        info["robot_module"] = None
        info["ok"] = False
        info["problems"].append("Robot Framework (módulo Python) não encontrado. Instale robotframework.")

    if not info["robot_cmd"]:
        info["ok"] = False
        info["problems"].append("Comando 'robot' não encontrado no PATH. Verifique instalação/venv.")

    # validação de melhor esforço dos requirements via importação
    try:
        with open(requirements_path, "r", encoding="utf-8", errors="ignore") as f:
            req_text = f.read()
        pkgs = _parse_requirements(req_text)
        for pkg in pkgs:
            imp_ok = _import_ok(pkg)
            dist_ok = _dist_ok(pkg)
            if imp_ok or dist_ok:
                info["packages_ok"].append(pkg)
                if (not imp_ok) and dist_ok:
                    info["packages_installed_but_import_failed"].append(pkg)
            else:
                info["packages_missing"].append(pkg)
        if info["packages_missing"]:
            info["ok"] = False
            info["problems"].append(
                "Algumas bibliotecas do requirements.txt parecem ausentes (melhor esforço via importação)."
            )

        if info["packages_installed_but_import_failed"]:
            info["ok"] = False
            info["problems"].append(
                "Algumas bibliotecas estão instaladas, mas falharam ao importar (pode indicar incompatibilidade com sua versão do Python)."
            )
    except Exception as e:
        info["ok"] = False
        info["problems"].append(f"Falha ao ler/validar requirements.txt: {e}")

    # Node é opcional (algumas suítes podem não precisar), mas avisa
    if not info["node_cmd"]:
        info["problems"].append("Node.js não encontrado no PATH (opcional, pode ser necessário em alguns cenários).")
    if not info["npm_cmd"]:
        info["problems"].append("NPM não encontrado no PATH (opcional).")

    return info