"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="max-w-md">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h2 className="text-xl font-semibold">Something went wrong</h2>
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          An error occurred while loading this page
        </p>
        <div className="space-y-4">
          <div className="rounded-md bg-muted p-3">
            <p className="text-sm font-mono text-muted-foreground">
              {error.message}
            </p>
          </div>
          <Button onClick={reset} className="w-full">
            Try again
          </Button>
        </div>
      </Card>
    </div>
  );
}
