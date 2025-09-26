from fastapi import FastAPI
import uvicorn

app = FastAPI(title='DT-RAG Test API', version='1.8.1')

@app.get('/')
async def root():
    return {'message': 'GitHub Codespace에서 실행 중인 DT-RAG 테스트 API', 'status': 'running'}

@app.get('/health')
async def health():
    return {'status': 'healthy', 'environment': 'GitHub Codespace'}

@app.post('/api/v1/search')
async def search(query: dict):
    return {
        'message': 'GitHub Codespace 테스트 완료',
        'query': query.get('query', 'test'),
        'results': ['테스트 결과 1', '테스트 결과 2']
    }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8002)
