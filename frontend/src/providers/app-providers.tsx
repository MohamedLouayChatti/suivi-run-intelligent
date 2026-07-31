"use client";

import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/providers/query-provider";
import { useTheme } from "@/hooks/use-theme";
import { AuthTokenBridge } from "@/lib/auth";

export function AppProviders({ children }: { children: React.ReactNode }) {
  useTheme();

  return (
    <QueryProvider>
      <AuthTokenBridge />
      <TooltipProvider>{children}</TooltipProvider>
    </QueryProvider>
  );
}
