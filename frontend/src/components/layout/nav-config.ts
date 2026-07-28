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

export const primaryNavItems: NavItem[] = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Tickets", href: "/tickets", icon: Ticket },
  { title: "History", href: "/history", icon: History },
  { title: "Chatbot", href: "/chatbot", icon: MessageSquare },
  { title: "Analytics", href: "/analytics", icon: BarChart3 },
];

export const administrationNavItems: NavItem[] = [
  { title: "Users", href: "/admin/users", icon: Users },
  { title: "Roles", href: "/admin/roles", icon: ShieldCheck },
  { title: "Audit", href: "/admin/audit", icon: ScrollText },
];

export const settingsNavItem: NavItem = {
  title: "Settings",
  href: "/settings",
  icon: Settings,
};
