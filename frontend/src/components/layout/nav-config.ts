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

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
}

export const primaryNavGroupLabel = "Opérations";

export const primaryNavItems: NavItem[] = [
  { title: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
  { title: "Tickets", href: "/tickets", icon: Ticket },
  { title: "Historique", href: "/history", icon: History },
  { title: "Chatbot", href: "/chatbot", icon: MessageSquare },
  { title: "Analyses", href: "/analytics", icon: BarChart3 },
];

export const administrationNavGroupLabel = "Administration";

export const administrationNavItems: NavItem[] = [
  { title: "Utilisateurs", href: "/admin/users", icon: Users },
  { title: "Rôles", href: "/admin/roles", icon: ShieldCheck },
  { title: "Audit", href: "/admin/audit", icon: ScrollText },
];

export const settingsNavItem: NavItem = {
  title: "Paramètres",
  href: "/settings",
  icon: Settings,
};
