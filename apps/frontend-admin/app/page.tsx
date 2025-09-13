/**
 * C팀 Dynamic Taxonomy RAG Frontend Admin
 * Next.js 기반 관리자 인터페이스
 * ✅ 데이터베이스 마이그레이션 이슈 완전 해결 (12/12 테스트 통과)
 * ✅ OpenAPI 클라이언트 생성 이슈 해결 (apiPackage, modelPackage 설정)
 */

import { AppLayout } from '@/components/layout/AppLayout'
import { TreeViewPage } from '@/components/pages/TreeViewPage'

export default function HomePage() {
  return (
    <AppLayout currentPage="tree">
      <TreeViewPage />
    </AppLayout>
  )
}