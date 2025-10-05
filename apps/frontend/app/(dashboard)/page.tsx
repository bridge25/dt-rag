export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          RAG System Overview and Statistics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-muted-foreground">
            Total Documents
          </h3>
          <p className="text-2xl font-bold">1,234</p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-muted-foreground">
            Active Agents
          </h3>
          <p className="text-2xl font-bold">5</p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-muted-foreground">
            Search Queries
          </h3>
          <p className="text-2xl font-bold">8,421</p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-muted-foreground">
            Avg Response Time
          </h3>
          <p className="text-2xl font-bold">245ms</p>
        </div>
      </div>
    </div>
  );
}
