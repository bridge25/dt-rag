
# 대화형 인입형 **에이전트 공장** 계획서 v1.0
> Conversation‑First Ingestion → Autonomous Research → RAG Store → Agent Generation  
> “말 한마디면, 신뢰 가능한 전문가 에이전트가 스스로 지식을 **찾아 채우고** 바로 **일한다**.”

---

## 0) 기획 의도 (Why now)
- 기존 RAG/챗봇은 **이미 가진 문서**를 “업로드/연결”해야만 작동함. 초기 가치 도달 시간(TTV)이 길다.
- 우리의 목표는 **“문서를 넣는 도구”가 아니라 “문서를 *찾아* 채워주는 도구”**다.  
- 핵심 가치는 **신뢰(인용·버전·신선도)**와 **속도(TTV 단축)**, **운영 가능성(관찰성·정책·Shadow)**.

## 1) 제품 정의 (One‑liner & JTBD)
- **One‑liner**: “원하는 전문가를 말하면, 시스템이 리서치 플랜을 세우고 신뢰 가능한 지식을 자동 수집·정리·인용해 **전문가 에이전트**를 즉시 만든다.”
- **JTBD**: *“나는 특정 문제 영역에서 신뢰 가능한 전문가형 에이전트를 빠르게 띄워, 반복 업무/의사결정을 자동화하고 싶다.”*

## 2) 차별화 포인트 (Wedge)
1. **대화형 인입(Conversation‑First)**: 말 한마디 → 스코프/소스/증거수준/신선도 자동 설계.
2. **커버리지 미터**: 무엇을 채웠고, 어디가 비었는지를 %로 시각화 + “자동 보강” 버튼.
3. **Evidence Receipt(근거 영수증) + 확신도**: 모든 답변에 출처 카드 + 수집 시각 + 확신도 배지.
4. **Shadow Mode(무중단 파일럿)**: 실사용 로그와 에이전트 제안을 나란히 비교·학습.
5. **정책/라이선스 엔진**: 소스별 수집/보관/표시 규칙(OA/유료/사내용) 내장.

## 3) 목표 (Business & Product)
- **TTV**: “제로 상태 → 유용한 에이전트” **2시간 이내** (기존 대비 −60% 이상).
- **인용률**: 98%+ (출처 없는 문장 금지).
- **커버리지**: 초기 목표 토픽 대비 ≥ 80% 채움.
- **업데이트 지연**: 핵심 소스 < 24h.
- **파일럿 효과**: 재문의율 −25% / 에스컬레이션 −20% / p95 지연 −30%.

---

## 4) 사용자 여정 & UX 플로우
### 4.1 온보딩 위저드(5단계, 15분)
1) **한 줄 주문**: “ICT 트레이딩형 BTC 투자자 에이전트 만들어줘.”  
2) **스코프**: 도메인·대상·지역/규정·타임프레임·리스크(보수/표준/도전).  
3) **소스/권한**: 공개 소스(기본) + 사용자 소유 유료 소스(키 연결).  
4) **신선도·빈도**: 소스별 모니터링 주기(예: 가이드라인/8h/24h).  
5) **미리보기**: 예상 커버리지·필요 API키/비용·완료 ETA(분) 표시 → **“인입 시작”**.

### 4.2 진행 화면
- **진행률 바 + 커버리지 미터**(토픽 매트릭스)  
- **리서치 플랜 카드**(수집→청킹→태깅→색인 단계별 로그)  
- **정책 경고**: 라이선스 제한/미갱신 소스 배지

### 4.3 사용 화면
- **메인 답변 카드**: 답변 본문 → 하단 **영수증(출처 2–3개 + 수집 시각 + 확신도)**  
- **Second Opinion 탭**: 보수안/도전안 나란히 제시 + “부담 줄이기” 버튼  
- **빨간 실 맵**: 내 서사 타임라인(질문→결정→결과)  
- **Shadow 스위치**: “사람 답변 vs 에이전트 제안” 나란히 보기

---

## 5) 기술 아키텍처 (개요)
```
User ──> Ingestion Wizard ──> Research Planner ──┬─> Source Connectors/Crawlers
                                                  │
                                                  ├─> Preprocessor (Chunking/Tagging/Summarizer)
                                                  │
                                                  ├─> Policy/Licensing Engine (allow/transform/deny)
                                                  │
                                                  └─> Indexer (BM25 + Vector + Reranker)
                                                          │
                                                          ├─> RAG Store (Chunks, Metadata, Versions)
                                                          └─> Coverage Meter (Topic Matrix & Gaps)

Agent Runtime ──> Retriever Orchestrator ──> Composer ──> Evidence Receipt + Confidence
                                       └─> Shadow Logger / Observability
```

### 5.1 코어 서비스
- **Research Planner**: 입력(목표) → 스코프/소스 매핑 → 수집/전처리/색인 파이프라인 생성
- **Policy/Licensing Engine**: 소스별 *수집/보관/표시* 룰 적용(OA/유료/사내 한정)
- **Coverage Meter**: 도메인 스키마(토픽×속성) 대비 채움률 계산·시각화
- **Observability**: 인용률·인용누락·업데이트 지연·Shadow 일치율·실패 Top‑N

---

## 6) 구현 방법 (스프린트 제안)
### Phase 0 — 스켈레톤(1주)
- Ingestion Wizard(폼/프롬프트) + Planner v0(룰 기반 소스 매핑)  
- 크롤러(사이트맵/URL/파일) + 청킹(규칙/LLM 하이브리드)  
- RAG Store 스키마 v0 + BM25/Vector 인덱싱
- Evidence Receipt UX v0, 간이 대시보드(인용률/커버리지)

### Phase 1 — 운영화(2주)
- Policy/Licensing Engine(룰 테이블 + 변환 파이프)  
- Shadow Mode(이중 로그 + 비교 리포트)  
- Coverage Auto‑Fill(공백 → 추천 소스/키워드)  
- 업데이트 워처(소스별 스케줄러 + 변경 감지)

### Phase 2 — 최적화(2주)
- Planner v1(템플릿+룰+경험치) / 재랭커 추가  
- 관찰성 보강(지연·비용·실패 Top‑N, 미갱신 차단 옵션)  
- 템플릿 마켓(Agent Recipes) 10종

---

## 7) API/이벤트 사양(요약)
### 7.1 Ingestion
- `POST /plans` — {goal, domain, scope, sources, freshness} → {plan_id, steps, ETA}
- `POST /ingestions` — {plan_id} → {run_id, progress_stream}
- `GET /coverage/{agent_id}` — 토픽 매트릭스/커버률
- `POST /sources` — 파일/URL/사이트맵/커넥터 등록(스케줄 포함)

### 7.2 Policy/Licensing
- `POST /policies` — {source_id, access: OA|Licensed|Internal, transform: {quote|summary|link_only}}  
- `GET /violations` — 위반 로그(차단/대체/요약 전환)

### 7.3 Retrieval/Answering
- `POST /query` — {agent_id, q} → {answer, evidence[], confidence, trace_id}
- `GET /traces/{trace_id}` — 플랜/리트리브 경로/코스트/지연

### 7.4 Shadow/Observability
- `POST /shadow` — {conversation_id, human_answer, agent_answer, verdict}  
- `GET /metrics` — {coverage, citation_rate, stale_rate, shadow_agreement, p95, cost}

---

## 8) 데이터 모델(요약)
### 8.1 Chunk
```json
{
  "chunk_id": "...",
  "text": "...",
  "source_id": "...",
  "source_url": "...",
  "collected_at": "2025-10-11T09:00:00Z",
  "version": "esmo_2025.1",
  "topic": ["암종:유방", "병기:IIIA", "전략:수술전보조"],
  "evidence_level": "guideline|review|primary",
  "jurisdiction": "US|EU|KR",
  "confidence": 0.82,
  "license": "OA|Licensed|Internal",
  "display_rule": "quote|summary|link_only"
}
```

### 8.2 Coverage Matrix(개념)
- 축 A: 도메인 토픽(예: 암종/병기/라인, 혹은 ICT 개념 목록)  
- 축 B: 근거 유형(가이드라인/리뷰/원저) × 최신성(연도/버전)  
- 지표: `coverage = (#충족 셀) / (#타깃 셀)`

---

## 9) 품질 보증 & 평가
- **수용 기준(Acceptance)**  
  - 인용률 ≥ 98%, 커버리지 ≥ 80%, 업데이트 지연 < 24h, Shadow 일치 ≥ 85%  
- **테스트 세트**: 도메인별 50문항 벤치마크(정답/부분정답/오답 정의 포함)
- **A/B**: 밴딧/디베이트/리트리버 전략별 품질·지연·비용 비교
- **경고 규칙**: 출처 0개/신선도 만료/정책 위반 시 답변 축약 또는 차단

---

## 10) 보안·법·컴플라이언스
- **정책 엔진 우선 적용**: 유료/폐쇄형은 링크·메타만(요약은 사용자 권한 있을 때).  
- **PII/비식별화**: 업로드·로그 모두 PII 마스킹 옵션.  
- **감사 추적**: 모든 답변은 trace_id로 수집 경로·근거·버전을 역추적 가능.

---

## 11) 운영/관찰성 대시보드
- **핵심 위젯**: 인용률, 인용누락 Top‑N, 커버리지 스파크라인, 갱신 지연, Shadow 일치율, 실패 사유 트리맵  
- **알림**: 미갱신 소스, 대량 정책 위반, 급격한 품질 저하

---

## 12) 리스크와 대응
| 리스크 | 영향 | 대응 |
|---|---|---|
| 빅벤더 모방 | 차별성 약화 | **커버리지 미터/Shadow/정책 엔진** 같은 운영 UX를 데이터 자산으로 심화 |
| 크롤러 유지비 | 원가 상승 | 상위 30개 소스 집중 + BYO 파이프라인(웹훅/SDK) |
| 환각/오정보 | 신뢰 붕괴 | 출처 없는 문장 금지 + 확신도 배지 + 고위험 도메인 축약 |
| 라이선스 | 법적 리스크 | 소스별 룰·감사, Unpaywall 등 OA 우선, 사용자 권한 위임 |
| 시의성 | 가치 하락 | 소스별 SLA 표시, 미갱신 차단 옵션, 워처 알람 |

---

## 13) 가격·패키징(GTM 요지)
- **Team**: 월정액 + 사용량(인입/질의), 커넥터 3종, 기본 대시보드.
- **Enterprise**: 온프레/VPC, SSO/SOC2 패키지, 정책·감사·권한 상속, 전용 SLA.
- **가치증명**: 온보딩 인건비·재작업 감소 vs 구독료 계산기 제공.

---

## 14) 체크리스트 (요약)
### A. 빌드 준비
- [ ] 토픽 스키마 정의(도메인 1종)  
- [ ] 크롤러 3종(URL/사이트맵/파일)  
- [ ] 청킹 파이프라인(규칙+LLM)  
- [ ] RAG Store 스키마(v0)  
- [ ] Evidence Receipt UI v0

### B. 파일럿 전
- [ ] 벤치마크 50문항/정답 기준 합의  
- [ ] 정책 룰 기본셋(OA/유료/사내)  
- [ ] Shadow 로깅 켜기  
- [ ] 커버리지 타깃 매트릭스 설정

### C. 파일럿 중(2주)
- [ ] 목표지표 대시보드 상시 확인  
- [ ] 실패·인용누락 Top‑N 주 2회 보강  
- [ ] 업데이트 지연 < 24h 유지

### D. 파일럿 후
- [ ] TTV/인용률/커버리지/Shadow 결과 보고서  
- [ ] 템플릿·소스·정책 개선 리비전  
- [ ] 가격 산정·도입 제안서 발행

---

## 15) 로드맵 (V0 → V2)
- **V0**: 대화형 위저드, 크롤러 3종, 커버리지 미터, 영수증, Shadow v0, 정책 룰 v0  
- **V1**: Planner v1(템플릿/룰/경험치), 재랭커, 관찰성 보강, 템플릿 마켓 10종  
- **V2**: 데이터 네트워킹(조직간 레시피 교환/프라이빗 마켓), 자동 CoT 평가, 다국어 확장

---

### 부록 A) Agent Recipe 스펙(요약)
```yaml
recipe:
  name: "ICT_BTC_Scalper_v1"
  scope:
    domain: "crypto_trading"
    timeframe: ["M5","H1"]
    risk_profile: "balanced"
  sources:
    - type: "api"
      id: "binance_futures"
      freshness: "1m"
    - type: "web"
      url: "https://innercircletrader.com/..."
      freshness: "7d"
  policies:
    - source: "binance_futures"
      license: "internal"
      display: "quote"
  retrieval:
    strategy: ["bm25","vector","rerank"]
  compose:
    guardrails: ["no_personal_financial_advice"]
```

### 부록 B) Shadow 평가 템플릿(요약)
- 샘플 100 케이스: (상황/질문/사람답/에이전트답/판정)  
- 지표: 일치율, 보정 필요 규칙, 인용 누락 사유 분류(자료부족/정책차단/신선도 만료)

---

**한 줄 요약**:  
**“찾아와서 채워준다 + 인용으로 증명한다 + Shadow로 안전하게 확장한다”** — 이 세 축을 수치로 달성하는 것이 본 계획의 전부다.
