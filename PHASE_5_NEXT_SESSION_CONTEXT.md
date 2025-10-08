# Phase 5 - LangGraph Integration Next Session Context

## Session Starting Point

**Last Completed**: Phase 4.2 TreeViewer Extended Features (DiffViewer, RollbackDialog, HITLQueue)

**Current Phase**: Phase 5 - LangGraph 7-Step RAG Orchestration Integration

**Session Date**: 2025-10-06

## Phase 5 Objective

Integrate existing LangGraph 7-step RAG orchestration workflow into main API endpoints, replacing mock implementations with real pipeline execution.

### 7-Step Workflow Specification
1. **Intent Classification** - Understand user query intent
2. **Retrieval** - Fetch relevant documents using hybrid search
3. **Planning** - Determine response strategy
4. **Tool Execution** - Execute MCP tools if needed
5. **Composition** - Generate response with LLM
6. **Citation** - Add source references
7. **Response** - Return final structured output

## Files Already Implemented (Phase 4.2 Complete)

### Backend
- `apps/api/services/taxonomy_service.py` (Lines 235-292: compare_versions method)
- `apps/api/routers/taxonomy_router.py` (Existing endpoints verified)

### Frontend
- `apps/frontend-admin/src/services/taxonomyService.ts` (Lines 89-116: compareVersions client method)
- `apps/frontend-admin/src/components/tree/DiffViewer.tsx` (122 lines - version diff visualization)
- `apps/frontend-admin/src/components/tree/RollbackDialog.tsx` (131 lines - rollback safety dialog)
- `apps/frontend-admin/src/components/tree/HITLQueue.tsx` (207 lines - HITL review interface)

## Phase 5 Implementation Checklist

### Step 1: Information Gathering (IG)
- [ ] Read `apps/orchestration/src/langgraph_pipeline.py` - Understand existing 7-step workflow structure
- [ ] Read PRD `prd_dynamic_taxonomy_rag_v_1_8 최종 (1).md` line 139+ for detailed 7-step specification
- [ ] Read `apps/api/routers/orchestration_router.py` - Identify mock implementations to replace
- [ ] Read `phase1~5.txt` lines 92-113 for Phase 5 scope and constraints
- [ ] Check existing state management patterns in LangGraph implementation

### Step 2: Service Layer Implementation
- [ ] Create `apps/api/services/langgraph_service.py`
  - Wrapper around existing `langgraph_pipeline.py`
  - Methods: `execute_7step_pipeline(query, context_params)`
  - Return schema: `{response, sources[], confidence, cost, latency, step_traces[]}`

### Step 3: API Router Integration
- [ ] Modify `apps/api/routers/orchestration_router.py`
  - Replace mock with `LangGraphService` calls
  - Endpoint: `POST /chat/run` (or similar endpoint name from current code)
  - Request schema: `{query, session_id?, taxonomy_filters?, topk?}`
  - Response schema: `{answer, sources[], metadata: {confidence, latency, cost}}`

### Step 4: Testing & Verification
- [ ] Test endpoint with curl: `POST /api/v1/chat/run -d '{"query":"What is machine learning?"}'`
- [ ] Verify all 7 steps execute in sequence
- [ ] Check step_traces returned in debug mode
- [ ] Validate sources[] contain chunk_id, doc_id, score, snippet

### Step 5: Error Handling & Edge Cases
- [ ] Handle LangGraph state errors gracefully
- [ ] Timeout handling (max execution time)
- [ ] Empty retrieval result handling
- [ ] Tool execution failures

## Key Technical Concepts

### LangGraph State Management
- **StateGraph**: Directed graph of processing steps
- **State Schema**: Typed dictionary passed between nodes
- **Conditional Edges**: Dynamic routing based on state values
- **Checkpointing**: Ability to save/resume workflow state

### Integration Patterns
- **Service Wrapper**: `langgraph_service.py` wraps existing pipeline, doesn't duplicate logic
- **Dependency Injection**: Use FastAPI `Depends()` for service injection
- **Async Execution**: All LangGraph steps should support async/await
- **Structured Logging**: Log each step's input/output for debugging

## Database Schema (Relevant to Phase 5)

### Documents Table
```python
class Document(Base):
    __tablename__ = "documents"
    doc_id: Mapped[uuid.UUID]
    filename: Mapped[Optional[str]]
    content: Mapped[Optional[str]]
```

### Chunks Table
```python
class Chunk(Base):
    __tablename__ = "chunks"
    chunk_id: Mapped[uuid.UUID]
    doc_id: Mapped[Optional[uuid.UUID]]
    text: Mapped[Optional[str]]
    embedding: Mapped[Optional[Vector(1536)]]
```

### DocTaxonomy Table (for taxonomy filtering)
```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"
    doc_id: Mapped[Optional[uuid.UUID]]
    node_id: Mapped[Optional[uuid.UUID]]
    path: Mapped[Optional[List[str]]]
    confidence: Mapped[Optional[float]]
```

## API Endpoints Current State

### Working Endpoints (Phase 1-4)
- `GET /api/v1/taxonomy/versions` - List taxonomy versions
- `GET /api/v1/taxonomy/{version}/tree` - Get full tree
- `GET /api/v1/taxonomy/{base_version}/compare/{target_version}` - Version diff
- `GET /api/v1/classify/hitl/tasks` - Get HITL review queue
- `POST /api/v1/classify/hitl/review` - Submit HITL review

### To Be Implemented (Phase 5)
- `POST /api/v1/chat/run` (or similar) - Execute 7-step LangGraph pipeline

## Known Configuration

### API Server
- **Base URL**: `http://localhost:8001/api/v1`
- **API Key**: `7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y`
- **Database**: PostgreSQL at `localhost:5433/dt_rag_test`

### Frontend Admin
- **Framework**: Next.js 15 App Router
- **UI Library**: Tailwind CSS + shadcn/ui
- **Port**: 3000

## Phase 5 Non-Scope (Defer to Phase 6)

- ❌ MCP whitelist/blacklist configuration
- ❌ Custom tool registration interface
- ❌ Multi-turn conversation state persistence
- ❌ Advanced caching strategies

## Definition of Done (DoD)

Phase 5 is complete when:

1. ✅ `apps/api/services/langgraph_service.py` created with pipeline wrapper
2. ✅ `POST /chat/run` endpoint integrated with real LangGraph execution
3. ✅ Response schema includes: `{answer, sources[], metadata: {confidence, cost, latency}}`
4. ✅ All 7 steps execute in sequence (verified via step_traces or logs)
5. ✅ curl test succeeds: `POST /chat/run -d '{"query":"test query"}'` returns 200 with sources
6. ✅ Error handling for retrieval failures, tool errors, LLM timeouts
7. ✅ File count ≤ 5 new/modified files

## First Actions for Next Session

**Immediate Next Steps**:

1. Read existing LangGraph implementation:
   ```bash
   Read apps/orchestration/src/langgraph_pipeline.py
   ```

2. Read PRD 7-step specification:
   ```bash
   Read prd_dynamic_taxonomy_rag_v_1_8 최종 (1).md (lines 139+)
   ```

3. Read current orchestration router:
   ```bash
   Read apps/api/routers/orchestration_router.py
   ```

4. Read Phase 5 scope:
   ```bash
   Read phase1~5.txt (lines 92-113)
   ```

5. After IG complete, create service wrapper:
   ```bash
   Write apps/api/services/langgraph_service.py
   ```

## Important Notes

- **No assumptions**: Always read actual code, never assume structure
- **바이브코딩 methodology**: Follow "바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md" principles
- **CLAUDE.md compliance**: No guessing, read all code directly, fix all errors immediately
- **Existing pipeline**: DO NOT recreate LangGraph workflow - wrap existing implementation
- **Service layer pattern**: Create thin service wrapper, delegate to existing orchestration code

## Expected Timeline

- **IG Phase**: ~30 minutes (read 4 key files)
- **Service Creation**: ~20 minutes (wrapper implementation)
- **Router Integration**: ~15 minutes (replace mock)
- **Testing**: ~15 minutes (curl tests, error scenarios)
- **Total**: ~1.5 hours estimated

## Success Criteria

Phase 5 successful if:
- User can call `POST /chat/run` with natural language query
- System executes all 7 steps (intent→retrieve→plan→tools→compose→cite→respond)
- Response includes generated answer + source citations
- Latency < 5 seconds for typical query
- Error messages are actionable (not generic 500 errors)

---

**Ready to begin Phase 5 LangGraph Integration**

Start with: "phase 5 시작하자" or "IG 시작"
