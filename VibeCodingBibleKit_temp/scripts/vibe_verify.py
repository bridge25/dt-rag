#!/usr/bin/env python3
import subprocess, os, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run(cmd):
    try:
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        return {"cmd": " ".join(cmd), "code": res.returncode, "out": res.stdout, "err": res.stderr}
    except FileNotFoundError as e:
        return {"cmd": " ".join(cmd), "code": 127, "out": "", "err": str(e)}

reports = []
# 러프/마이파이/pytest 등은 프로젝트에 있을 때만 실행
if os.path.exists(os.path.join(ROOT, "pyproject.toml")):
    reports.append(run(["ruff", "check", "."]))
    reports.append(run(["mypy", "."]))
if os.path.exists(os.path.join(ROOT, "pytest.ini")) or os.path.exists(os.path.join(ROOT, "tests")):
    reports.append(run(["pytest", "-q"]))

print(json.dumps({"verify": reports}, ensure_ascii=False, indent=2))
