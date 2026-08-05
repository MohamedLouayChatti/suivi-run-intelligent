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
  /** Hard admin-role gate — mirrors the backend's `require_admin` on the underlying pages. */
  adminOnly?: boolean;
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
  { title: "Analyses", href: "/analytics", icon: BarChart3 },
];

export const administrationNavGroupLabel = "Administration";

export const administrationNavItems: NavItem[] = [
  { title: "Utilisateurs", href: "/admin/users", icon: Users, requires: { adminOnly: true } },
  { title: "Rôles", href: "/admin/roles", icon: ShieldCheck, requires: { adminOnly: true } },
  { title: "Audit", href: "/admin/audit", icon: ScrollText, requires: { adminOnly: true, permission: "audit.read" } },
];

export const settingsNavItem: NavItem = {
  title: "Paramètres",
  href: "/settings",
  icon: Settings,
};
