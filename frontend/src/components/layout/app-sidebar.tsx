"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { ChevronRight, PanelLeftIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
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
  useSidebar,
} from "@/components/ui/sidebar";
import {
  administrationNavGroupLabel,
  administrationNavItems,
  primaryNavGroupLabel,
  primaryNavItems,
  routeRequirements,
  settingsNavItem,
  type NavItem,
} from "@/components/layout/nav-config";
import { usePermissions } from "@/lib/auth";

/**
 * Expanded: the logo links home as before, with its own collapse button beside the title.
 * Collapsed: there is no room for a separate button, so the logo itself becomes the expand
 * trigger -- hovering swaps it to a panel icon (same affordance ChatGPT uses on its sidebar),
 * and clicking expands instead of navigating.
 */
function SidebarBrand() {
  const { state, toggleSidebar } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <>
      <Link
        href="/dashboard"
        onClick={(event) => {
          if (isCollapsed) {
            event.preventDefault();
            toggleSidebar();
          }
        }}
        aria-label={isCollapsed ? "Développer la barre latérale" : undefined}
        className="group/logo flex min-w-0 flex-1 items-center gap-2.5 px-2"
      >
        <span className="relative flex h-8 shrink-0 items-center justify-center group-data-[collapsible=icon]:h-6">
          <Image
            src="/icon_sofrecom_logo.png"
            alt="Logo Sofrecom"
            width={139}
            height={150}
            priority
            className="h-8 w-auto object-contain transition-opacity duration-150 group-data-[collapsible=icon]:h-6 group-data-[collapsible=icon]:group-hover/logo:opacity-0"
          />
          <PanelLeftIcon
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 m-auto flex size-4 items-center justify-center text-sidebar-foreground opacity-0 transition-opacity duration-150 group-data-[collapsible=icon]:group-hover/logo:opacity-100"
          />
        </span>
        <span className="truncate text-[15px] font-semibold tracking-tight group-data-[collapsible=icon]:hidden">
          Suivi Run
        </span>
      </Link>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={toggleSidebar}
        aria-label="Réduire la barre latérale"
        className="shrink-0 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:hidden"
      >
        <PanelLeftIcon />
      </Button>
    </>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const { hasPermission, hasAnyPermission } = usePermissions();

  // Read from `routeRequirements` rather than from the item, so the sidebar and the page it
  // links to are gated by one declaration. An entry with no requirement is open to anyone
  // signed in.
  function isVisible(item: NavItem): boolean {
    const requirement = routeRequirements[item.href];
    if (!requirement) return true;
    if (requirement.permission && !hasPermission(requirement.permission)) return false;
    if (requirement.anyPermission && !hasAnyPermission(requirement.anyPermission)) return false;
    return true;
  }

  const visiblePrimaryNavItems = primaryNavItems.filter(isVisible);
  const visibleAdministrationNavItems = administrationNavItems.filter(isVisible);

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 flex-row items-center border-b border-sidebar-border">
        <SidebarBrand />
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
          <>
            {/* Expanded: grouped under a collapsible label, same as the provided design. */}
            <SidebarGroup className="group-data-[collapsible=icon]:hidden">
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

            {/* Collapsed: SidebarMenuSub is display:none in icon mode and has no tooltip
                fallback, which is what hid these icons entirely -- render the same items as
                top-level buttons instead, exactly like the primary nav and Paramètres do. */}
            <SidebarGroup className="hidden group-data-[collapsible=icon]:flex">
              <SidebarGroupContent>
                <SidebarMenu className="gap-1">
                  {visibleAdministrationNavItems.map((item) => (
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
          </>
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
