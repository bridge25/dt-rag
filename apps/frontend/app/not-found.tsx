/**
 * 404 Not Found page with Ethereal Glass aesthetic
 *
 * @CODE:FRONTEND-002
 */

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileQuestion, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6 bg-dark-navy relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

      <Card className="max-w-md w-full relative z-10 border-white/10 bg-white/5 backdrop-blur-xl shadow-glass">
        <div className="flex flex-col items-center text-center p-8 space-y-6">
          <div className="relative">
            <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full" />
            <div className="relative bg-white/5 p-4 rounded-full border border-white/10">
              <FileQuestion className="h-10 w-10 text-blue-400" />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-white tracking-tight">Page not found</h2>
            <p className="text-white/60">
              The page you are looking for does not exist or has been moved to another dimension.
            </p>
          </div>

          <Link href="/" className="w-full">
            <Button className="w-full bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 border border-blue-500/50" size="lg">
              <Home className="mr-2 h-4 w-4" />
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
