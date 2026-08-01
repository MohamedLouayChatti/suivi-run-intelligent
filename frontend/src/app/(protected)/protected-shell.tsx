"use client";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { SiteHeader } from "@/components/layout/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AuthGate, useCurrentUser, useLogout } from "@/lib/auth";

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/**
 * Client-side UI shell (sidebar/header) plus the AuthGate that waits for GET /auth/me to
 * confirm the signed-in Clerk user maps to a recognized application user. The Clerk session
 * check itself now happens one level up in layout.tsx via auth.protect() (resource-based,
 * per Clerk's createRouteMatcher deprecation) — this component only handles what comes after.
 */
function ProtectedShell({ children }: { children: React.ReactNode }) {
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const displayName = user?.displayName ?? "";

  return (
    <AuthGate>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <SiteHeader
            userName={displayName}
            userRole={user?.roles[0]?.name ?? ""}
            userInitials={initials(displayName)}
            onLogout={logout}
          />
          <div className="flex flex-1 flex-col bg-surface">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </AuthGate>
  );
}

export { ProtectedShell };
