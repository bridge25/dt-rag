# ⚠️ DEPRECATED - SVG 아바타 시스템

**상태**: DEPRECATED (2025-11-28)
**현재 사용 중인 에셋**: `/public/assets/agents/nobg/`

---

## 이 폴더의 SVG 아바타는 현재 사용되지 않습니다.

### 현재 Agent Cards에서 사용 중인 이미지

```
/public/assets/agents/nobg/
├── common/robot-common-01.png ~ 04.png
├── rare/robot-rare-01.png ~ 04.png
├── epic/robot-epic-01.png ~ 04.png
└── legendary/robot-legendary-01.png ~ 04.png
```

### 이 폴더 vs 현재 사용 폴더

| 항목 | 이 폴더 (avatars/robots/) | 현재 사용 (assets/agents/nobg/) |
|------|--------------------------|-------------------------------|
| 포맷 | SVG (벡터) | PNG (래스터, 투명 배경) |
| 개수 | 16개 캐릭터 | 16개 로봇 |
| 스타일 | 추상적 캐릭터 아이콘 | AI 생성 포토리얼리스틱 로봇 |
| 사용처 | 미사용 | Agent Cards 페이지 |

### 왜 이 폴더가 deprecated 되었나요?

1. **디자인 변경**: 뉴디자인1.png에서 포토리얼리스틱 로봇 이미지 사용
2. **rembg 처리**: AI로 배경 제거된 투명 PNG 사용
3. **시각적 일관성**: Ethereal Glass 테마와 더 잘 어울림

### 향후 계획

- 이 SVG 아바타들은 다른 용도(예: 프로필 아이콘)로 재사용 가능
- 현재 Agent Cards 페이지에서는 사용하지 않음
- 삭제하지 않고 보관 (향후 활용 가능성)

---

**참고 문서**:
- `/apps/frontend/DESIGN-SYSTEM.md` - 최신 디자인 가이드
- `NANOBANANA_PROMPTS.md` - SVG 생성 프롬프트 (참고용)
