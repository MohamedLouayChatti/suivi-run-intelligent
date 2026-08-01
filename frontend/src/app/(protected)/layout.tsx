"use client";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { SiteHeader } from "@/components/layout/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { useCurrentUser } from "@/hooks/use-current-user";
import { mockRoles } from "@/features/roles/mock-data";
import { getRoleName } from "@/features/users/mock-data";
import { AuthGate, useLogout } from "@/lib/auth";

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = useCurrentUser();
  const logout = useLogout();

  return (
    <AuthGate>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <SiteHeader
            userName={user.display_name}
            userRole={getRoleName(user, mockRoles)}
            userInitials={initials(user.display_name)}
            onLogout={logout}
          />
          <div className="flex flex-1 flex-col bg-surface">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </AuthGate>
  );
}
