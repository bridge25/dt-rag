#!/usr/bin/env python3
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
manifest = os.path.join(ROOT, ".vibe", "context_manifest.json")
if not os.path.exists(manifest):
    print("먼저 vibe_context_load 를 실행하세요.", file=sys.stderr)
    sys.exit(1)

with open(manifest, "r", encoding="utf-8") as f:
    m = json.load(f)

# 상위 MI 파일에서 4~5개를 제안
candidates = [f["path"] for f in m["files"] if f["mi_hint"] > 0][:5]
plan = {
    "plan_files": candidates,
    "definition_of_done": [
        "린터/타입체크 통과",
        "필수 유닛 테스트 추가/갱신",
        "성능/보안 체크(수치 포함)",
    ],
    "notes": "최대 5파일 내에서 작은 커밋 단위를 유지하세요."
}
print(json.dumps(plan, ensure_ascii=False, indent=2))
