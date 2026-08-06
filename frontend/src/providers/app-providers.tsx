"use client";

import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { QueryProvider } from "@/providers/query-provider";
import { useTheme } from "@/hooks/use-theme";
import { AuthTokenBridge, AuthFailureBridge } from "@/lib/auth";
import { NotificationsSseBridge } from "@/features/notifications/notifications-sse-bridge";

export function AppProviders({ children }: { children: React.ReactNode }) {
  useTheme();

  return (
    <QueryProvider>
      <AuthTokenBridge />
      <AuthFailureBridge />
      <NotificationsSseBridge />
      <TooltipProvider>{children}</TooltipProvider>
      <Toaster />
    </QueryProvider>
  );
}
