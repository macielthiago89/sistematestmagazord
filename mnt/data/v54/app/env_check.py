from __future__ import annotations

import os
import re
import sys
import json
import platform
import importlib
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
    # best-effort mapping between pip name and import name
    mapping = {
        "robotframework": "robot",
        "Pillow": "PIL",
        "pywin32": "win32api",
        "python-dotenv": "dotenv",
        "google-auth-oauthlib": "google_auth_oauthlib",
        "google-auth": "google.auth",
        "robotframework-databaselibrary": "DatabaseLibrary",
        "robotframework-faker": "FakerLibrary",
        "robotframework-retryfailed": "RetryFailed",
        "robotframework-sikulilibrary": "SikuliLibrary",
    }
    mod = mapping.get(pkg, pkg)
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False

def run_checks(project_dir: str, requirements_path: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_exe": sys.executable,
        "robot_cmd": _which("robot"),
        "pip_cmd": _which("pip"),
        "node_cmd": _which("node"),
        "npm_cmd": _which("npm"),
        "adb_cmd": _which("adb"),
        "ok": True,
        "problems": [],
        "packages_missing": [],
        "packages_ok": [],
    }

    # robot python module check
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

    # requirements best-effort import validation
    try:
        with open(requirements_path, "r", encoding="utf-8", errors="ignore") as f:
            req_text = f.read()
        pkgs = _parse_requirements(req_text)
        for pkg in pkgs:
            if _import_ok(pkg):
                info["packages_ok"].append(pkg)
            else:
                info["packages_missing"].append(pkg)
        if info["packages_missing"]:
            info["ok"] = False
            info["problems"].append(
                "Algumas bibliotecas do requirements.txt parecem ausentes (best-effort via import)."
            )
    except Exception as e:
        info["ok"] = False
        info["problems"].append(f"Falha ao ler/validar requirements.txt: {e}")

    # Node is optional (some suites may not need), but warn
    if not info["node_cmd"]:
        info["problems"].append("Node.js não encontrado no PATH (opcional, pode ser necessário em alguns cenários).")
    if not info["npm_cmd"]:
        info["problems"].append("NPM não encontrado no PATH (opcional).")

    return info
