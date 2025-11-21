/**
 * 404 Not Found page
 *
 * @CODE:FRONTEND-001
 */

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="max-w-md">
        <div className="flex items-center gap-2 mb-4">
          <FileQuestion className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Page not found</h2>
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          The page you are looking for does not exist
        </p>
        <Link href="/">
          <Button className="w-full">
            Go to Dashboard
          </Button>
        </Link>
      </Card>
    </div>
  );
}
