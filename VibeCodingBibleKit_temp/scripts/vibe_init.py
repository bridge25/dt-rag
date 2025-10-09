#!/usr/bin/env python3
import json, os, time, yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIBE_DIR = os.path.join(ROOT, ".vibe")
os.makedirs(VIBE_DIR, exist_ok=True)

cfg_path = os.path.join(ROOT, "vibe.config.yaml")
cfg = {}
if os.path.exists(cfg_path):
    try:
        import yaml  # type: ignore
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        cfg = {}

session = {
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "io_ratio_min": cfg.get("io_ratio_min", 20),
    "rules": cfg.get("rules", {}),
    "notes": [
        "I/O≥20:1, 가정·추측 금지, SOT=코드, 작은 커밋(≤5파일)",
        "구현 대화와 검증 대화 분리"
    ]
}
with open(os.path.join(VIBE_DIR, "session.json"), "w", encoding="utf-8") as f:
    json.dump(session, f, ensure_ascii=False, indent=2)

print("[vibe_init] 세션 생성:", os.path.join(VIBE_DIR, "session.json"))
