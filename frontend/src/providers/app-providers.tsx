"use client";

import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/providers/query-provider";
import { useTheme } from "@/hooks/use-theme";

export function AppProviders({ children }: { children: React.ReactNode }) {
  useTheme();

  return (
    <QueryProvider>
      <TooltipProvider>{children}</TooltipProvider>
    </QueryProvider>
  );
}
