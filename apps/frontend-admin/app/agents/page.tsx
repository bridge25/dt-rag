import { AppLayout } from '@/components/layout/AppLayout'
import { AgentFactory } from '@/components/agents/AgentFactory'

export default function AgentsPage() {
  return (
    <AppLayout currentPage="agents">
      <AgentFactory />
    </AppLayout>
  )
}