"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import {
  administrationNavGroupLabel,
  administrationNavItems,
  primaryNavGroupLabel,
  primaryNavItems,
  settingsNavItem,
  type NavItem,
} from "@/components/layout/nav-config";
import { usePermissions } from "@/lib/auth";

export function AppSidebar() {
  const pathname = usePathname();
  const { hasPermission } = usePermissions();

  function isVisible(item: NavItem): boolean {
    if (!item.requires) return true;
    if (item.requires.permission && !hasPermission(item.requires.permission)) return false;
    return true;
  }

  const visiblePrimaryNavItems = primaryNavItems.filter(isVisible);
  const visibleAdministrationNavItems = administrationNavItems.filter(isVisible);

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 justify-center border-b border-sidebar-border">
        <Link href="/dashboard" className="flex items-center gap-2.5 px-2">
          <Image
            src="/icon_sofrecom_logo.png"
            alt="Logo Sofrecom"
            width={139}
            height={150}
            priority
            className="h-8 w-auto shrink-0 object-contain group-data-[collapsible=icon]:h-6"
          />
          <span className="truncate text-[15px] font-semibold tracking-tight group-data-[collapsible=icon]:hidden">
            Suivi Run
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="uppercase tracking-wide">
            {primaryNavGroupLabel}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {visiblePrimaryNavItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname.startsWith(item.href)}
                    tooltip={item.title}
                  >
                    <Link href={item.href}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {visibleAdministrationNavItems.length > 0 && (
          <SidebarGroup>
            <Collapsible defaultOpen className="group/collapsible">
              <SidebarGroupLabel asChild className="uppercase tracking-wide">
                <CollapsibleTrigger className="flex w-full items-center">
                  {administrationNavGroupLabel}
                  <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
                </CollapsibleTrigger>
              </SidebarGroupLabel>
              <CollapsibleContent>
                <SidebarGroupContent>
                  <SidebarMenu className="gap-1">
                    <SidebarMenuItem>
                      <SidebarMenuSub className="gap-1">
                        {visibleAdministrationNavItems.map((item) => (
                          <SidebarMenuSubItem key={item.href}>
                            <SidebarMenuSubButton
                              asChild
                              isActive={pathname.startsWith(item.href)}
                            >
                              <Link href={item.href}>
                                <item.icon />
                                <span>{item.title}</span>
                              </Link>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </Collapsible>
          </SidebarGroup>
        )}

        <SidebarGroup className="mt-2 border-t border-sidebar-border pt-3">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={pathname.startsWith(settingsNavItem.href)}
                  tooltip={settingsNavItem.title}
                >
                  <Link href={settingsNavItem.href}>
                    <settingsNavItem.icon />
                    <span>{settingsNavItem.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
