import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Ticket,
  History,
  MessageSquare,
  BarChart3,
  Settings,
  Users,
  ShieldCheck,
  ScrollText,
} from "lucide-react";

export interface NavItemRequirement {
  /** A single permission name the current user's effective permissions must include. */
  permission?: string;
}

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  /** Unset means always visible to any authenticated user. */
  requires?: NavItemRequirement;
}

export const primaryNavGroupLabel = "Opérations";

export const primaryNavItems: NavItem[] = [
  { title: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
  { title: "Tickets", href: "/tickets", icon: Ticket, requires: { permission: "ticket.read" } },
  { title: "Historique", href: "/history", icon: History, requires: { permission: "ticket.read" } },
  { title: "Chatbot", href: "/chatbot", icon: MessageSquare },
  { title: "Analyses", href: "/analytics", icon: BarChart3, requires: { permission: "analytics.read" } },
];

export const administrationNavGroupLabel = "Administration";

// "Administration" is a grouping label for the user, not an authorization concept: each item
// below names the breadth permission its page's endpoints actually require. Nothing here keys
// off a role, so granting e.g. `audit.read` to a non-Admin role reveals exactly that one entry.

export const administrationNavItems: NavItem[] = [
  { title: "Utilisateurs", href: "/admin/users", icon: Users, requires: { permission: "user.read_all" } },
  { title: "Rôles", href: "/admin/roles", icon: ShieldCheck, requires: { permission: "role.read_all" } },
  { title: "Audit", href: "/admin/audit", icon: ScrollText, requires: { permission: "audit.read" } },
];

export const settingsNavItem: NavItem = {
  title: "Paramètres",
  href: "/settings",
  icon: Settings,
};
