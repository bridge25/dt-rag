# Client Generation Guide

OpenAPI v1.8.1 스키마로부터 TypeScript 및 Python 클라이언트를 생성하는 방법입니다.

## 필수 도구 설치

```bash
# TypeScript/JavaScript 클라이언트 생성기
npm install -g @openapitools/openapi-generator-cli

# Python 클라이언트 생성기 (pip으로)
pip3 install openapi-generator-cli
```

## 클라이언트 생성 명령어

### TypeScript 클라이언트
```bash
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g typescript-axios \
  -o generated/typescript-client \
  --additional-properties=npmName=dynamic-taxonomy-rag-client
```

### Python 클라이언트
```bash
openapi-generator-cli generate \
  -i docs/openapi.yaml \
  -g python \
  -o generated/python-client \
  --additional-properties=packageName=dynamic_taxonomy_rag_client
```

## 생성된 클라이언트 사용법

### TypeScript 예제
```typescript
import { DefaultApi, Configuration } from 'dynamic-taxonomy-rag-client';

const config = new Configuration({
  basePath: 'http://localhost:8000'
});
const api = new DefaultApi(config);

// 분류 요청
const classifyResponse = await api.classifyPost({
  chunk_id: "chunk_001",
  text: "머신러닝 모델을 사용한 RAG 시스템 구축"
});
```

### Python 예제
```python
import dynamic_taxonomy_rag_client
from dynamic_taxonomy_rag_client.api import default_api
from dynamic_taxonomy_rag_client.model.classify_request import ClassifyRequest

configuration = dynamic_taxonomy_rag_client.Configuration(
    host="http://localhost:8000"
)

with dynamic_taxonomy_rag_client.ApiClient(configuration) as api_client:
    api_instance = default_api.DefaultApi(api_client)
    classify_request = ClassifyRequest(
        chunk_id="chunk_001",
        text="머신러닝 모델을 사용한 RAG 시스템 구축"
    )
    
    api_response = api_instance.classify_post(classify_request)
```

## 검증

생성된 클라이언트가 OpenAPI v1.8.1 계약과 일치하는지 확인:

```bash
# Pydantic 모델과 계약 일치 확인
cd packages/common-schemas
python3 -c "from models import *; print('✓ 모든 모델 import 성공')"
```