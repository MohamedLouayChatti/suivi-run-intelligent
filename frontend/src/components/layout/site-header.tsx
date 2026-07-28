import { Bell, Search, UserRound } from "lucide-react";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-4">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />

      <span className="text-sm font-semibold whitespace-nowrap">
        AI Support Intelligence Platform
      </span>

      <div className="relative ml-4 flex-1 max-w-sm">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search" className="pl-8" disabled />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Button variant="ghost" size="icon" disabled aria-label="Notifications">
          <Bell />
        </Button>
        <Button variant="ghost" size="icon" disabled aria-label="User profile">
          <UserRound />
        </Button>
      </div>
    </header>
  );
}
