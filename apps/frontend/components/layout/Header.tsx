import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b px-6">
      <div className="flex-1">
        <h2 className="text-lg font-semibold">Welcome to DT-RAG</h2>
      </div>
      <div className="flex items-center gap-4">
        <ThemeToggle />
      </div>
    </header>
  );
}
