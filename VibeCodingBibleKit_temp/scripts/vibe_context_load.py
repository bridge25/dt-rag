#!/usr/bin/env python3
import os, json, hashlib, fnmatch, time, yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIBE_DIR = os.path.join(ROOT, ".vibe")
os.makedirs(VIBE_DIR, exist_ok=True)

with open(os.path.join(ROOT, "vibe.config.yaml"), "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

include_exts = set(cfg["context"]["include_extensions"])
exclude_dirs = set(cfg["context"]["exclude_dirs"])

def should_skip_dir(d):
    return any(part in exclude_dirs for part in d.replace("\\","/").split("/"))

def mi_hint(path):
    # 간단한 힌트: 파일 확장자/경로에 기반한 추정 점수
    score = 0
    if any(seg in path.lower() for seg in ["api", "router", "service", "schema", "interface", "controller"]):
        score += 3
    if os.path.basename(path).lower() in ["README.md".lower(), "vibe.config.yaml"]:
        score += 2
    if any(path.endswith(ext) for ext in [".ts", ".tsx", ".py"]):
        score += 1
    return score

files = []
for root, dirs, fs in os.walk(ROOT):
    # 2-depth 제한
    depth = len(os.path.relpath(root, ROOT).split(os.sep))
    if depth > 3:
        dirs[:] = []  # stop descending
    # exclude
    if should_skip_dir(root):
        dirs[:] = []
        continue
    for name in fs:
        p = os.path.join(root, name)
        if not any(p.endswith(ext) for ext in include_exts):
            continue
        stat = os.stat(p)
        files.append({
            "path": os.path.relpath(p, ROOT).replace("\\", "/"),
            "size": stat.st_size,
            "mi_hint": mi_hint(p),
            "mtime": int(stat.st_mtime)
        })

# 간단 정렬: mi_hint(desc), size(desc)
files.sort(key=lambda x: (x["mi_hint"], x["size"]), reverse=True)

manifest = {
    "generated_at": int(time.time()),
    "root": ROOT,
    "files": files[:500]  # 상한
}

out = os.path.join(VIBE_DIR, "context_manifest.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print("[vibe_context_load] 컨텍스트 매니페스트:", out, f"({len(files)} files scanned)")
