/**
 * Application providers for React Query, theme management, and i18n
 *
 * @CODE:FRONTEND-001
 * @CODE:FRONTEND-REDESIGN-001
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { useState, type ReactNode } from "react";
import { Toaster } from "sonner";
import { I18nProvider } from "@/lib/i18n/context";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        retry: 1,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <I18nProvider defaultLanguage="en">
          {children}
          <Toaster richColors position="top-right" />
        </I18nProvider>
      </NextThemesProvider>
    </QueryClientProvider>
  );
}
