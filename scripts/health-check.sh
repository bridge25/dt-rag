#!/bin/bash
# 시스템 헬스체크 스크립트

set -e

API_URL="http://localhost:8000"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

echo "🏥 시스템 헬스체크를 시작합니다..."
echo

# API 서비스 확인
echo "📡 API 서비스 확인..."
if curl -s "$API_URL/health" > /dev/null; then
    echo "✅ API 서비스: 정상"
    
    # 상세 헬스체크
    HEALTH_RESPONSE=$(curl -s "$API_URL/system/health")
    echo "📊 상세 상태:"
    echo "$HEALTH_RESPONSE" | jq '.'
else
    echo "❌ API 서비스: 응답 없음"
fi

echo

# 데이터베이스 확인
echo "🗄️ 데이터베이스 확인..."
if docker exec dt-rag-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: 정상"
else
    echo "❌ PostgreSQL: 응답 없음"
fi

# Redis 확인
echo "📦 Redis 확인..."
if docker exec dt-rag-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: 정상"
else
    echo "❌ Redis: 응답 없음"
fi

echo

# 모니터링 서비스 확인
echo "📈 모니터링 서비스 확인..."

if curl -s "$PROMETHEUS_URL" > /dev/null; then
    echo "✅ Prometheus: 정상"
else
    echo "❌ Prometheus: 응답 없음"
fi

if curl -s "$GRAFANA_URL" > /dev/null; then
    echo "✅ Grafana: 정상"
else
    echo "❌ Grafana: 응답 없음"
fi

echo

# 컨테이너 상태 확인
echo "🐳 컨테이너 상태:"
docker-compose ps

echo

# 리소스 사용량 확인
echo "💻 시스템 리소스:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo

# 최근 로그 확인 (에러만)
echo "📝 최근 에러 로그:"
docker-compose logs --since=10m 2>&1 | grep -i error | tail -5 || echo "에러 로그 없음"

echo
echo "🎯 헬스체크 완료"