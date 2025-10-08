# DT-RAG 프론트엔드 사용자 가이드

## 🌐 프론트엔드 접속

**URL**: http://localhost:3000

---

## 📱 사용 가능한 페이지

### 1. Dashboard (홈)
**URL**: http://localhost:3000

**기능**:
- 실시간 시스템 상태 확인
  - System Status: 전체 시스템 상태
  - Database: PostgreSQL + pgvector 연결 상태
  - Cache: Redis 연결 상태
- Quick Actions
  - Search Documents 링크
  - Upload Documents 링크

**테스트 방법**:
1. 브라우저에서 http://localhost:3000 접속
2. System Status 카드에 "healthy" 표시 확인
3. Database 카드에 "connected" 표시 확인
4. Redis 카드에 "connected" 표시 확인

---

### 2. Search (검색)
**URL**: http://localhost:3000/search

**기능**:
- Hybrid Search (BM25 + Vector)
- Keyword-only Search (BM25)
- Top K Results 설정 (1-100)
- 검색 결과 표시 (Score, Text, Metadata)

**테스트 방법**:

#### Step 1: 기본 검색
1. Search 페이지 접속
2. Query 입력란에 검색어 입력:
   ```
   machine learning
   ```
3. Top K Results: 5 (기본값)
4. "Use Hybrid Search" 체크박스 활성화 (기본)
5. **"Search"** 버튼 클릭
6. 결과 확인:
   - 검색 결과 개수 표시
   - 각 결과의 Score (유사도)
   - Chunk ID
   - Text content
   - Metadata (문서 정보)

#### Step 2: Keyword-only 검색
1. "Use Hybrid Search" 체크박스 **해제**
2. Query: `RAG system`
3. **"Search"** 클릭
4. BM25만 사용한 결과 확인

#### Step 3: 다양한 검색어 테스트
```
- "vector embeddings"
- "taxonomy classification"
- "document processing"
- "natural language"
```

---

### 3. Documents (문서 업로드)
**URL**: http://localhost:3000/documents

**기능**:
- Drag & Drop 파일 업로드
- 다중 파일 업로드 지원
- 실시간 업로드 진행상황 표시
- 지원 형식: TXT, PDF, DOCX, MD

**테스트 방법**:

#### 준비: 테스트용 문서 생성
Windows 탐색기에서:
```
C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\sample_docs\
```

이미 3개의 샘플 문서가 있습니다:
- `rag_overview.txt` - RAG 시스템 개요
- `taxonomy_guide.txt` - Taxonomy 가이드
- `vector_embeddings.txt` - Vector embeddings 설명

#### Step 1: 파일 선택 업로드
1. Documents 페이지 접속
2. "Click to upload" 영역 클릭
3. 파일 선택 대화상자에서 `rag_overview.txt` 선택
4. 업로드 진행상황 확인:
   - Progress bar 표시
   - 완료 시 체크 아이콘 표시
   - Document ID와 chunks 개수 표시

#### Step 2: Drag & Drop 업로드
1. Windows 탐색기에서 `taxonomy_guide.txt` 파일 선택
2. 브라우저의 업로드 영역으로 드래그
3. 영역이 파란색으로 변경됨 확인
4. 파일 Drop
5. 자동 업로드 시작 확인

#### Step 3: 다중 파일 업로드
1. "Click to upload" 클릭
2. Ctrl 키를 누른 채 여러 파일 선택
3. 열기 클릭
4. Upload Queue에 모든 파일 표시 확인
5. 각 파일의 개별 진행상황 확인

#### Step 4: 새 문서 만들어서 테스트
Windows 메모장에서 새 파일 생성:

**파일명**: `test_document.txt`
**내용**:
```
Machine Learning and AI

Machine learning is a subset of artificial intelligence that enables
computers to learn from data without being explicitly programmed.

Key concepts:
- Supervised learning
- Unsupervised learning
- Neural networks
- Deep learning

Applications:
- Image recognition
- Natural language processing
- Recommendation systems
```

저장 후 프론트엔드에서 업로드 테스트!

---

### 4. Monitoring (시스템 모니터링)
**URL**: http://localhost:3000/monitoring

**기능**:
- 시스템 메트릭 확인
- API 응답 시간
- 에러 로그

---

### 5. Taxonomy (분류 체계)
**URL**: http://localhost:3000/taxonomy

**기능**:
- 문서 분류 체계 시각화
- DAG 구조 확인

---

## 🎯 완전한 테스트 시나리오

### 시나리오 1: 문서 업로드 → 검색 플로우

#### 1단계: 문서 업로드
1. http://localhost:3000/documents 접속
2. `sample_docs` 폴더의 모든 파일 업로드
3. 각 문서의 Document ID 기록:
   - rag_overview.txt → doc_id_1
   - taxonomy_guide.txt → doc_id_2
   - vector_embeddings.txt → doc_id_3

#### 2단계: 검색 테스트
1. http://localhost:3000/search 접속
2. 검색어 입력: `RAG system architecture`
3. 검색 실행
4. 결과에서 업로드한 문서의 내용이 나오는지 확인
5. Score 확인 (높은 순서대로 정렬됨)

#### 3단계: 다양한 검색
```
Query 1: "vector embeddings"
→ vector_embeddings.txt의 내용이 상위에 나와야 함

Query 2: "taxonomy classification"
→ taxonomy_guide.txt의 내용이 상위에 나와야 함

Query 3: "machine learning"
→ 업로드한 test_document.txt의 내용이 나와야 함
```

---

### 시나리오 2: Hybrid vs Keyword Search 비교

#### 준비: 의미가 유사하지만 단어가 다른 검색
검색어: `"information retrieval"`

**Hybrid Search (활성화)**:
- Vector similarity로 의미적으로 유사한 문서 찾음
- "document search", "knowledge base" 같은 유사 개념도 검색됨

**Keyword Search (비활성화)**:
- 정확히 "information retrieval" 단어가 포함된 문서만 찾음
- 더 정확하지만 범위가 좁음

#### 테스트:
1. Query: `information retrieval`
2. Hybrid Search 활성화 → 결과 기록
3. Hybrid Search 비활성화 → 결과 기록
4. 결과 비교!

---

## 🎨 UI/UX 특징

### 반응형 디자인
- 데스크톱, 태블릿, 모바일 모두 지원
- 브라우저 창 크기 조절해서 확인 가능

### 다크모드 지원
- (구현되어 있다면) 우측 상단 테마 토글 버튼

### 실시간 업데이트
- Dashboard의 시스템 상태는 60초마다 자동 갱신
- 검색 결과는 즉시 표시

---

## 🐛 예상 가능한 문제 해결

### 1. 검색 결과가 없어요
**원인**: 아직 문서가 업로드되지 않음
**해결**:
1. Documents 페이지에서 문서 업로드
2. 업로드 완료 후 검색 재시도

### 2. 업로드가 실패해요
**원인**: API 연결 문제 또는 파일 형식 오류
**해결**:
1. 파일 형식 확인 (TXT, PDF, DOCX, MD만 지원)
2. 파일 크기 확인 (10MB 이하)
3. 브라우저 콘솔 (F12) 에러 확인

### 3. Dashboard가 "Loading..." 상태에서 멈춤
**원인**: API 서버 연결 불가
**해결**:
1. API 서버 상태 확인: http://localhost:8000/health
2. 컨테이너 상태 확인: `docker ps`
3. API 로그 확인: `docker logs dt_rag_api`

---

## 🔍 고급 기능 (개발자용)

### 브라우저 개발자 도구 사용

#### 1. Network 탭에서 API 호출 확인
1. F12 키 → Network 탭
2. 검색 또는 업로드 실행
3. API 요청/응답 확인:
   - Request Headers (X-API-Key 포함)
   - Response Body (검색 결과 JSON)
   - Status Code (200, 403, etc.)

#### 2. Console 탭에서 에러 확인
1. F12 키 → Console 탭
2. 빨간색 에러 메시지 확인
3. API Error 로그 확인

#### 3. Application 탭에서 캐시 확인
1. F12 키 → Application 탭
2. Local Storage / Session Storage 확인
3. 캐시된 API 응답 확인 (React Query)

---

## 📊 성능 측정

### 검색 응답 시간 확인
1. F12 → Network 탭
2. 검색 실행
3. `/api/v1/search/` 요청 클릭
4. Timing 탭에서 응답 시간 확인
   - **목표**: < 200ms (p95)

### 업로드 속도 확인
1. 큰 파일 (예: 5MB PDF) 업로드
2. Network 탭에서 업로드 시간 확인
3. Progress bar 진행 확인

---

## 🎉 체험 체크리스트

사용자 입장에서 모든 기능을 체험했는지 확인:

- [ ] Dashboard에서 시스템 상태 확인
- [ ] 샘플 문서 3개 업로드 성공
- [ ] Hybrid Search로 검색 테스트
- [ ] Keyword Search로 검색 테스트
- [ ] 검색 결과에서 Score와 Metadata 확인
- [ ] 새 문서 만들어서 업로드
- [ ] 업로드한 새 문서가 검색되는지 확인
- [ ] Drag & Drop 업로드 테스트
- [ ] 다중 파일 업로드 테스트
- [ ] Top K 값 변경해서 검색 (5, 10, 20)
- [ ] 다양한 검색어로 테스트 (최소 5개)

---

## 💡 추천 테스트 순서

### 초급 (10분)
1. Dashboard 확인
2. 샘플 문서 1개 업로드
3. 간단한 검색 1-2회

### 중급 (20분)
1. 모든 샘플 문서 업로드
2. Hybrid vs Keyword 비교 검색
3. Top K 변경 테스트
4. 새 문서 작성 후 업로드

### 고급 (30분+)
1. 다양한 형식 문서 업로드 (TXT, PDF, DOCX)
2. 복잡한 검색 쿼리 테스트
3. 브라우저 개발자 도구로 API 호출 분석
4. 성능 측정 및 비교

---

**작성일**: 2025-10-08
**프론트엔드 버전**: Next.js 14
**Status**: Production Ready ✅
