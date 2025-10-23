# Vibe Coding Bible Kit (v1)

바이브코딩을 항상 같은 방식으로 수행하기 위한 실행 키트입니다.

## 빠른 시작
1. `python scripts/vibe_init.py` — 세션 초기화(.vibe/session.json)
2. `python scripts/vibe_context_load.py` — 2-depth 인덱싱 → .vibe/context_manifest.json
3. `python scripts/vibe_plan.py` — 4–5파일 단위 계획(DoD 포함)
4. (선택) **설명 모드**로 알고리즘 설명 후 승인 → 구현
5. `python scripts/vibe_verify.py` — 린터/테스트 실행 + 실패를 SentryBug 템플릿으로 출력

> 원칙: I/O ≥ 20:1, 단일 진실의 원천=코드, 가정·추측 금지, 작은 커밋(최대 5파일)
