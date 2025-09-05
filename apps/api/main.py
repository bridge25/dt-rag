"""
A팀 Dynamic Taxonomy RAG API Server
Bridge Pack 스펙 100% 준수 FastAPI MVP
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, classify, search, taxonomy

app = FastAPI(
    title="DT-RAG API",
    version="v2.0.0-rc1",
    description="A팀 Database & Taxonomy API - Bridge Pack 호환",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (Bridge Pack 엔드포인트)
app.include_router(health.router, tags=["Health"])
app.include_router(classify.router, tags=["Classification"])
app.include_router(search.router, tags=["Search"])
app.include_router(taxonomy.router, tags=["Taxonomy"])

@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "service": "DT-RAG API",
        "version": "v2.0.0-rc1",
        "team": "A",
        "spec": "OpenAPI v1.8.1",
        "schemas": "0.1.3",
        "status": "MVP Ready",
        "endpoints": [
            "GET /healthz",
            "GET /taxonomy/{version}/tree", 
            "POST /classify",
            "POST /search"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 A팀 DT-RAG API 서버 시작")
    print("📡 포트: 8000")
    print("📋 Bridge Pack 엔드포인트: /healthz, /classify, /search, /taxonomy/{version}/tree")
    print("📖 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)