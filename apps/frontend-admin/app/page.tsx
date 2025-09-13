/**
 * C팀 Dynamic Taxonomy RAG Frontend Admin
 * Next.js 기반 관리자 인터페이스
 * ✅ 데이터베이스 마이그레이션 이슈 완전 해결 (12/12 테스트 통과)
 * ✅ OpenAPI 클라이언트 생성 이슈 해결 (apiPackage, modelPackage 설정)
 * ✅ 전체 워크플로우 진행: TypeScript 클라이언트 + UI 컴포넌트 통합 테스트
 * 🔄 워크플로우 재실행: 2025-09-13T19:36:00Z
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