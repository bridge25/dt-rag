/**
 * Header component with theme toggle
 *
 * @CODE:FRONTEND-001
 */

import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between px-6 border-b border-white/5 bg-white/[0.02] backdrop-blur-sm">
      <div className="flex-1">
        <h2 className="text-lg font-medium text-white/90">Welcome to DT-RAG</h2>
      </div>
      <div className="flex items-center gap-4">
        <ThemeToggle />
      </div>
    </header>
  );
}
