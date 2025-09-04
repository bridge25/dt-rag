#!/bin/bash
# 데이터베이스 백업 스크립트

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="dt-rag-postgres"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

echo "📦 데이터베이스 백업을 시작합니다..."

# PostgreSQL 백업
docker exec $DB_CONTAINER pg_dump -U postgres dt_rag > "$BACKUP_DIR/dt_rag_backup_$DATE.sql"

# 백업 압축
gzip "$BACKUP_DIR/dt_rag_backup_$DATE.sql"

echo "✅ 백업 완료: $BACKUP_DIR/dt_rag_backup_$DATE.sql.gz"

# 7일 이상된 백업 파일 삭제
find $BACKUP_DIR -name "dt_rag_backup_*.sql.gz" -mtime +7 -delete

echo "🧹 오래된 백업 파일을 정리했습니다"