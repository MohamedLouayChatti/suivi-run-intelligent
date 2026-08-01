"use client";

import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/providers/query-provider";
import { useTheme } from "@/hooks/use-theme";
import { AuthTokenBridge, AuthFailureBridge } from "@/lib/auth";

export function AppProviders({ children }: { children: React.ReactNode }) {
  useTheme();

  return (
    <QueryProvider>
      <AuthTokenBridge />
      <AuthFailureBridge />
      <TooltipProvider>{children}</TooltipProvider>
    </QueryProvider>
  );
}
