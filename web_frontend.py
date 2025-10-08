#!/usr/bin/env python3
"""
Dynamic Taxonomy RAG - 웹 프론트엔드
실제 사용자가 웹 브라우저에서 체험할 수 있는 HTML/CSS/JavaScript UI
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx
import json

app = FastAPI(title="Dynamic Taxonomy RAG - Web Frontend")

# 백엔드 API 서버 주소
BACKEND_URL = "http://localhost:8002"

@app.get("/", response_class=HTMLResponse)
async def home():
    """메인 웹 인터페이스"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Dynamic Taxonomy RAG System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .content {
            padding: 40px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        .section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        .section h2 {
            color: #495057;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
            width: 100%;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            background: white;
            border: 2px solid #28a745;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
        }
        .error {
            background: #f8d7da;
            border: 2px solid #dc3545;
            color: #721c24;
        }
        .loading {
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }
        .api-status {
            grid-column: 1 / -1;
            text-align: center;
            padding: 20px;
            background: #d1ecf1;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .feature-grid {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e9ecef;
            transition: transform 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        @media (max-width: 768px) {
            .content { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Dynamic Taxonomy RAG System</h1>
            <p>실제 풀 기능을 웹 브라우저에서 체험해보세요!</p>
            <p>버전 1.8.1 - 프로덕션 준비 완료</p>
        </div>

        <div class="content">
            <div class="api-status">
                <h3>🟢 백엔드 API 서버: http://localhost:8002</h3>
                <p>풀 기능 Dynamic Taxonomy RAG API가 실행 중입니다</p>
                <button onclick="checkApiStatus()">API 상태 확인</button>
            </div>

            <!-- 검색 섹션 -->
            <div class="section">
                <h2>🔍 하이브리드 검색</h2>
                <p>BM25 + Vector Search 통합 검색</p>
                <div class="form-group">
                    <label>검색어</label>
                    <input type="text" id="searchQuery" placeholder="검색하고 싶은 내용을 입력하세요" value="artificial intelligence">
                </div>
                <div class="form-group">
                    <label>최대 결과 수</label>
                    <select id="maxResults">
                        <option value="3">3개</option>
                        <option value="5" selected>5개</option>
                        <option value="10">10개</option>
                    </select>
                </div>
                <button onclick="performSearch()">🔍 검색 실행</button>
                <div id="searchResult"></div>
            </div>

            <!-- 분류 섹션 -->
            <div class="section">
                <h2>📊 문서 분류</h2>
                <p>ML 기반 자동 문서 분류</p>
                <div class="form-group">
                    <label>분류할 텍스트</label>
                    <textarea id="classifyText" rows="4" placeholder="분류하고 싶은 문서 내용을 입력하세요">This is a technical documentation about machine learning algorithms and artificial intelligence systems.</textarea>
                </div>
                <div class="form-group">
                    <label>신뢰도 임계값</label>
                    <input type="range" id="confidenceThreshold" min="0.1" max="1.0" step="0.1" value="0.7">
                    <span id="confidenceValue">0.7</span>
                </div>
                <button onclick="classifyDocument()">📊 분류 실행</button>
                <div id="classifyResult"></div>
            </div>

            <!-- 기능 카드들 -->
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🗂️ 분류체계 조회</h3>
                    <p>계층적 분류 구조 확인</p>
                    <button onclick="getTaxonomy()">분류체계 보기</button>
                    <div id="taxonomyResult"></div>
                </div>

                <div class="feature-card">
                    <h3>📈 시스템 모니터링</h3>
                    <p>실시간 시스템 상태 확인</p>
                    <button onclick="getMonitoring()">상태 확인</button>
                    <div id="monitoringResult"></div>
                </div>

                <div class="feature-card">
                    <h3>🤖 AI 에이전트</h3>
                    <p>동적 에이전트 생성</p>
                    <button onclick="createAgent()">에이전트 생성</button>
                    <div id="agentResult"></div>
                </div>

                <div class="feature-card">
                    <h3>📖 API 문서</h3>
                    <p>Interactive Swagger UI</p>
                    <button onclick="window.open('http://localhost:8002/docs', '_blank')">문서 열기</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 신뢰도 슬라이더 업데이트
        document.getElementById('confidenceThreshold').addEventListener('input', function(e) {
            document.getElementById('confidenceValue').textContent = e.target.value;
        });

        // API 상태 확인
        async function checkApiStatus() {
            const resultDiv = document.querySelector('.api-status');
            resultDiv.innerHTML = '<div class="loading">API 상태 확인 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/health');
                const data = await response.json();
                resultDiv.innerHTML = `
                    <h3>✅ API 서버 정상 동작</h3>
                    <p>상태: ${data.status} | 버전: ${data.version}</p>
                    <p>모드: ${data.components ? data.components.database : 'unknown'}</p>
                `;
            } catch (error) {
                resultDiv.innerHTML = `
                    <h3>❌ API 서버 연결 실패</h3>
                    <p>백엔드 서버(http://localhost:8002)가 실행되지 않았습니다</p>
                `;
            }
        }

        // 검색 실행
        async function performSearch() {
            const query = document.getElementById('searchQuery').value;
            const maxResults = document.getElementById('maxResults').value;
            const resultDiv = document.getElementById('searchResult');

            if (!query.trim()) {
                resultDiv.innerHTML = '<div class="result error">검색어를 입력해주세요</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="loading">검색 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/api/v1/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        max_results: parseInt(maxResults)
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    let html = `<div class="result">
                        <h4>🔍 검색 결과 (${data.total_hits}개, ${data.search_time_ms.toFixed(2)}ms)</h4>
                        <p><em>${data.mode}</em></p>
                    `;

                    data.hits.forEach((hit, index) => {
                        html += `
                            <div style="border-top: 1px solid #dee2e6; padding-top: 15px; margin-top: 15px;">
                                <h5>${hit.title}</h5>
                                <p>${hit.content}</p>
                                <small>점수: ${hit.score} | 출처: ${hit.source}</small>
                            </div>
                        `;
                    });

                    html += '</div>';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = `<div class="result error">검색 실패: ${JSON.stringify(data)}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">검색 오류: ${error.message}</div>`;
            }
        }

        // 문서 분류
        async function classifyDocument() {
            const text = document.getElementById('classifyText').value;
            const threshold = document.getElementById('confidenceThreshold').value;
            const resultDiv = document.getElementById('classifyResult');

            if (!text.trim()) {
                resultDiv.innerHTML = '<div class="result error">분류할 텍스트를 입력해주세요</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="loading">분류 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/api/v1/classify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        confidence_threshold: parseFloat(threshold)
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    let html = `<div class="result">
                        <h4>📊 분류 결과 (신뢰도: ${(data.confidence * 100).toFixed(1)}%)</h4>
                        <p><em>${data.mode}</em></p>
                    `;

                    data.classifications.forEach(cls => {
                        html += `
                            <div style="border-top: 1px solid #dee2e6; padding-top: 10px; margin-top: 10px;">
                                <strong>${cls.category_name}</strong> (${(cls.confidence * 100).toFixed(1)}%)
                                <br><small>경로: ${cls.path.join(' > ')}</small>
                                <br><small>근거: ${cls.reasoning}</small>
                            </div>
                        `;
                    });

                    html += '</div>';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = `<div class="result error">분류 실패: ${JSON.stringify(data)}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">분류 오류: ${error.message}</div>`;
            }
        }

        // 분류체계 조회
        async function getTaxonomy() {
            const resultDiv = document.getElementById('taxonomyResult');
            resultDiv.innerHTML = '<div class="loading">조회 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/api/v1/taxonomy');
                const data = await response.json();

                resultDiv.innerHTML = `<div class="result" style="font-size: 12px;">
                    <strong>버전:</strong> ${data.version}<br>
                    <strong>총 노드:</strong> ${data.total_nodes}개<br>
                    <strong>최대 깊이:</strong> ${data.max_depth}단계<br>
                    <strong>루트:</strong> ${data.root.name}
                </div>`;
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">오류: ${error.message}</div>`;
            }
        }

        // 시스템 모니터링
        async function getMonitoring() {
            const resultDiv = document.getElementById('monitoringResult');
            resultDiv.innerHTML = '<div class="loading">확인 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/api/v1/monitoring/health');
                const data = await response.json();

                resultDiv.innerHTML = `<div class="result" style="font-size: 12px;">
                    <strong>상태:</strong> ${data.system_status}<br>
                    <strong>CPU:</strong> ${data.metrics ? data.metrics.cpu.usage_percent + '%' : 'N/A'}<br>
                    <strong>메모리:</strong> ${data.metrics ? data.metrics.memory.usage_percent + '%' : 'N/A'}
                </div>`;
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">오류: ${error.message}</div>`;
            }
        }

        // AI 에이전트 생성
        async function createAgent() {
            const resultDiv = document.getElementById('agentResult');
            resultDiv.innerHTML = '<div class="loading">생성 중...</div>';

            try {
                const response = await fetch('http://localhost:8002/api/v1/agents/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: 'Demo Agent',
                        type: 'document_analyzer',
                        config: { temperature: 0.7 }
                    })
                });

                const data = await response.json();

                resultDiv.innerHTML = `<div class="result" style="font-size: 12px;">
                    <strong>에이전트 ID:</strong> ${data.agent_id}<br>
                    <strong>상태:</strong> ${data.status}<br>
                    <strong>기능:</strong> ${data.capabilities ? data.capabilities.join(', ') : 'N/A'}
                </div>`;
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">오류: ${error.message}</div>`;
            }
        }

        // 페이지 로드 시 API 상태 확인
        window.onload = function() {
            checkApiStatus();
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    print("🌐 Dynamic Taxonomy RAG 웹 프론트엔드 시작...")
    print("📱 포트: 3000")
    print("🔗 백엔드 API: http://localhost:8002")
    print("🌍 웹 인터페이스: http://localhost:3000")
    print()
    print("✨ 브라우저에서 http://localhost:3000 접속하여")
    print("   실제 풀 기능을 웹 UI로 체험해보세요!")
    print()

    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")