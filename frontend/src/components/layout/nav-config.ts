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
  BrainCircuit,
} from "lucide-react";

export interface RouteRequirement {
  /** A single permission name the current user's effective permissions must include. */
  permission?: string;
  /**
   * At least one of these permission names. For a page that composes capabilities the backend
   * gates separately, where holding any one of them makes the page worth reaching — the entry
   * appears, and the page shows only the sections the caller's permissions cover.
   */
  anyPermission?: readonly string[];
}

/**
 * What each route requires, declared exactly once.
 *
 * The sidebar filters its entries against this and `RequireRouteAccess` gates the page against
 * the same entry, so the icon and the page can no longer disagree. They used to be declared
 * separately and had drifted: `/admin/users` appeared in the sidebar for anyone holding
 * `user.read_all`, then refused them unless they also held `role.read_all` and
 * `permission.read` — a caller granted the reach to see users met an Access Denied screen
 * instead of the page whose icon they had just been shown.
 *
 * Every requirement here is a permission name, never a role. A page reachable only by
 * administrators is one whose permissions only administrators happen to hold, which is a fact
 * about the seeded catalog rather than a rule in the UI — grant `audit.read` to another role
 * and exactly that entry appears for them, with no change here.
 *
 * These are also deliberately *narrow*: the least a caller needs for the page to be worth
 * opening, not everything any section of it might use. A conjunction of every permission the
 * page's queries touch is a role check wearing permission vocabulary — it admits only the
 * people who hold all of them, which is what "Admin" used to mean. Sections gate themselves.
 */
export const routeRequirements: Record<string, RouteRequirement> = {
  "/tickets": { permission: "ticket.read" },
  "/history": { permission: "ticket.read" },
  "/analytics": { permission: "analytics.read" },
  // Any one capability the page offers is reason to open it: the table needs `user.read`
  // (every seeded role holds it) and shows more with `user.read_all`, while each action —
  // activating, assigning a role, editing permissions or staffing — renders only for the
  // permission that performs it.
  "/admin/users": {
    anyPermission: [
      "user.read_all",
      "user.activate",
      "user.deactivate",
      "user.manage_organization",
      "role.assign",
      "permission.grant_to_user",
      "permission.revoke_from_user",
    ],
  },
  // Reading the roles at all needs `role.read_all`; editing what they grant is a further
  // permission the page asks for on its own.
  "/admin/roles": { permission: "role.read_all" },
  "/admin/audit": { permission: "audit.read" },
  // Three independent permissions on the backend, and the page holds a section for each pair:
  // batch import, and the recalculation schedule (read to see it, manage to change it or run a
  // pass). Any one of them is reason for the entry to appear.
  "/admin/knowledge-base": {
    anyPermission: [
      "knowledge_base.batch_import",
      "knowledge_base.read_recalculation",
      "knowledge_base.manage_recalculation",
    ],
  },
};

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

// "Administration" is a grouping label for the user, not an authorization concept: what each
// entry needs is in `routeRequirements` above, keyed by the same href the link points at.
export const administrationNavItems: NavItem[] = [
  { title: "Utilisateurs", href: "/admin/users", icon: Users },
  { title: "Rôles", href: "/admin/roles", icon: ShieldCheck },
  { title: "Audit", href: "/admin/audit", icon: ScrollText },
  { title: "Base de connaissances", href: "/admin/knowledge-base", icon: BrainCircuit },
];

export const settingsNavItem: NavItem = {
  title: "Paramètres",
  href: "/settings",
  icon: Settings,
};
