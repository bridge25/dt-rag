import { AppLayout } from '@/components/layout/AppLayout'
import { TreeViewPage } from '@/components/pages/TreeViewPage'

export default function HomePage() {
  return (
    <AppLayout currentPage="tree">
      <TreeViewPage />
    </AppLayout>
  )
}