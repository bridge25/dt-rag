# Implementation Plan: SPEC-NEURAL-001

@SPEC:NEURAL-001 @VERSION:0.1.0 @PLAN

---

## 마일스톤 구조

### Phase 2A.1: Vector Similarity Search SQL Implementation
**우선순위**: High
**의존성**: FOUNDATION-001 (완료)
**목표**: pgvector 기반 Vector 검색 쿼리 구현 및 검증

**작업 항목**:
1. CaseBank Vector 검색 SQL 쿼리 작성
   - pgvector `<=>` 연산자 활용
   - 코사인 유사도 계산 (1.0 - distance)
   - NULL 임베딩 필터링
2. AsyncSession 기반 Python 래퍼 함수 구현
   - `neural_case_search()` 메서드
   - asyncio.wait_for() 타임아웃 적용
3. 단위 테스트 작성
   - Vector 검색 쿼리 정확도 검증
   - 타임아웃 처리 검증
   - 빈 결과 핸들링 검증

**완료 조건**:
- Vector 검색 쿼리가 상위 K개 케이스를 유사도 순으로 반환
- 타임아웃 100ms 초과 시 빈 리스트 반환
- 단위 테스트 커버리지 100%

### Phase 2A.2: Hybrid Score Fusion Logic
**우선순위**: High
**의존성**: Phase 2A.1 완료
**목표**: BM25 + Vector 하이브리드 스코어 결합 로직 구현

**작업 항목**:
1. 스코어 정규화 함수 구현
   - BM25 스코어: Min-Max Scaling
   - Vector 스코어: 이미 0~1 (정규화 불필요)
2. 하이브리드 스코어 계산 함수
   - 가중치 적용 (Vector 0.7, BM25 0.3)
   - 중복 케이스 병합 로직
3. 결과 정렬 및 상위 K개 선택
4. 단위 테스트 작성
   - 스코어 계산 정확도 검증
   - 중복 케이스 병합 검증
   - 가중치 변경 시 동작 검증

**완료 조건**:
- 하이브리드 스코어가 올바른 가중치로 계산됨
- 중복 케이스가 case_id 기준으로 병합됨
- 상위 K개 결과가 정렬되어 반환됨

### Phase 2A.3: API Endpoint Extension and Integration
**우선순위**: High
**의존성**: Phase 2A.1, 2A.2 완료
**목표**: `/search/neural` 엔드포인트 추가 및 기존 검색 API 확장

**작업 항목**:
1. 새로운 엔드포인트 추가: `/search/neural`
   - Feature Flag 확인 로직
   - Neural 검색 서비스 호출
   - 에러 핸들링 및 Fallback
2. 기존 `/search` 엔드포인트 확장
   - `use_neural` 파라미터 추가
   - 하이브리드 검색 로직 통합
3. 응답 스키마 확장
   - `search_mode` 필드 추가 (neural, bm25, hybrid, bm25_fallback)
4. 통합 테스트 작성
   - Feature Flag ON/OFF 시 동작 검증
   - 하이브리드 검색 전체 흐름 검증
   - Fallback 시나리오 검증

**완료 조건**:
- `/search/neural` 엔드포인트가 정상 동작
- Feature Flag OFF 시 503 응답 반환
- 하이브리드 검색이 올바른 search_mode로 응답
- Fallback 시 에러 없이 BM25 결과 반환

### Phase 2A.4: Performance Optimization and Indexing
**우선순위**: Medium
**의존성**: Phase 2A.3 완료
**목표**: Vector 검색 성능 최적화 및 인덱스 생성

**작업 항목**:
1. pgvector 인덱스 생성 (IVFFlat)
   - 리스트 수 최적화 (데이터셋 크기 기반)
   - 인덱스 생성 마이그레이션 스크립트
2. 성능 벤치마크
   - Vector 검색 시간 측정 (케이스 1000개, 5000개, 10000개)
   - 하이브리드 검색 시간 측정
   - 동시 요청 처리 성능 측정
3. 타임아웃 튜닝
   - 실제 응답 시간 기반 타임아웃 조정
   - 인덱스 최적화 후 재측정

**완료 조건**:
- Vector 검색 시간 < 100ms (케이스 1000개 기준)
- 하이브리드 검색 시간 < 200ms
- pgvector 인덱스 생성 완료

### Phase 2A.5: Testing and Quality Assurance
**우선순위**: High
**의존성**: Phase 2A.4 완료
**목표**: 전체 기능 통합 테스트 및 품질 검증

**작업 항목**:
1. 12개 단위 테스트 작성
   - Vector 검색 (3개)
   - 하이브리드 스코어 (3개)
   - API 엔드포인트 (4개)
   - Fallback 처리 (2개)
2. 4개 통합 테스트 작성
   - 전체 검색 흐름 (2개)
   - Feature Flag 토글 (1개)
   - 성능 벤치마크 (1개)
3. 코드 리뷰 및 Linter 검증
   - mypy 타입 검증
   - black, isort 포맷팅
   - flake8 스타일 검증
4. 보안 검증
   - SQL 인젝션 방지 확인
   - API 인증 로직 검증

**완료 조건**:
- 단위 테스트 커버리지 100%
- 통합 테스트 커버리지 90% 이상
- Linter 및 타입 검증 통과
- 보안 취약점 없음

---

## 기술적 접근 방법

### 1. pgvector 활용 전략
- **코사인 유사도 연산자**: `<=>` 사용 (L2 거리 기반)
- **거리 → 유사도 변환**: `1.0 - distance` (0~1 범위 정규화)
- **인덱스 전략**: IVFFlat 인덱스 (리스트 수 = sqrt(total_rows))

### 2. 스코어 정규화
- **BM25 스코어**: Min-Max Scaling
  - `normalized_bm25 = (bm25_score - min_score) / (max_score - min_score)`
- **Vector 스코어**: 이미 0~1 범위 (정규화 불필요)
- **가중치 적용**: `0.7 * vector + 0.3 * bm25`

### 3. Fallback 전략
- **임베딩 실패**: OpenAI API 오류 시 BM25만 사용
- **Vector 검색 실패**: 타임아웃 또는 pgvector 오류 시 BM25로 Fallback
- **Feature Flag OFF**: 기존 BM25 검색 로직 유지

### 4. 성능 최적화
- **타임아웃 설정**: asyncio.wait_for(timeout=0.1)
- **병렬 처리**: BM25 + Vector 검색 비동기 병렬 실행 (asyncio.gather)
- **캐싱**: 임베딩 생성 결과 캐싱 (향후 확장)

---

## 아키텍처 설계

### 컴포넌트 구조
```
apps/api/
├── database.py
│   ├── CaseBank (모델)
│   └── generate_case_embedding() (임베딩 생성)
├── routers/
│   └── search_router.py
│       ├── /search (기존 BM25)
│       ├── /search/neural (NEW: Neural 검색)
│       └── SearchService.neural_search() (NEW)
└── env_manager.py
    └── neural_case_selector (Feature Flag)

services/
└── neural_case_selector.py (NEW)
    ├── neural_case_search()
    ├── hybrid_search()
    └── combine_scores()
```

### 데이터 흐름
```
User Request → FastAPI → SearchService
                             ↓
              [Feature Flag 확인: neural_case_selector]
                             ↓
                    ┌────────┴────────┐
                    │                 │
              [Flag ON]           [Flag OFF]
                    │                 │
                    ↓                 ↓
         Neural/Hybrid Search    BM25 Search
                    │                 │
                    ↓                 ↓
         [임베딩 생성 → Vector 검색]
                    │
                    ↓
         [BM25 검색 병렬 실행]
                    │
                    ↓
         [스코어 결합 → 정렬]
                    │
                    └─────────┬───────┘
                              ↓
                      SearchResponse
```

---

## 리스크 및 대응 방안

### 리스크 1: pgvector 성능 이슈
**증상**: Vector 검색 시간이 100ms 초과
**대응**:
1. IVFFlat 인덱스 생성 (리스트 수 튜닝)
2. 케이스 수 제한 (초기에는 상위 1000개만 검색)
3. 타임아웃 조정 (100ms → 150ms)

### 리스크 2: 임베딩 생성 실패
**증상**: OpenAI API 키 미설정 또는 네트워크 오류
**대응**:
1. BM25 검색으로 Fallback
2. 경고 로그 기록
3. 응답에 `search_mode: "bm25_fallback"` 명시

### 리스크 3: Feature Flag 관리 복잡도
**증상**: 여러 곳에서 Feature Flag 확인 로직 중복
**대응**:
1. Decorator 패턴 사용: `@require_feature_flag("neural_case_selector")`
2. Middleware 레벨에서 Feature Flag 검증
3. 환경 변수 기반 동적 활성화

### 리스크 4: 가중치 튜닝 필요성
**증상**: 0.7:0.3 가중치가 최적이 아닐 수 있음
**대응**:
1. A/B 테스트 프레임워크 구축 (향후)
2. 가중치를 환경 변수로 설정 가능하도록 확장
3. SPEC-EVAL-001과 연계하여 품질 메트릭 기반 튜닝

---

## 의존성 및 순서

### 선행 작업 (완료됨)
- ✅ FOUNDATION-001: CaseBank query_vector 필드 활성화
- ✅ DATABASE-001: PostgreSQL + pgvector 설정
- ✅ SEARCH-001: BM25 검색 기반 구현

### 후속 작업 (블로킹)
- PLANNER-001 확장: Meta-Planner에서 Neural CBR 활용
- Phase 2B: Soft Q-learning Bandit 통합

### 병렬 가능 작업
- EVAL-001: Neural 검색 품질 평가 메트릭 개발

---

## 배포 전략

### Feature Flag 기반 단계적 배포
1. **Stage 1**: Feature Flag OFF (기본값)
   - 기존 BM25 검색만 사용
   - Neural 검색 코드 배포 (비활성 상태)
2. **Stage 2**: 내부 테스트 (Feature Flag ON)
   - 개발 환경에서 Neural 검색 활성화
   - 성능 및 품질 검증
3. **Stage 3**: 카나리 배포 (10% 트래픽)
   - 일부 사용자에게 Neural 검색 제공
   - 메트릭 모니터링
4. **Stage 4**: 전면 배포 (100% 트래픽)
   - Feature Flag ON으로 전환
   - 모니터링 지속

---

**END OF PLAN**
