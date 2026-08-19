import {
  Ticket,
  MessageSquare,
  Paperclip,
  UserCheck,
  UserX,
  UserPlus,
  ShieldCheck,
  BrainCircuit,
  FileUp,
  type LucideIcon,
} from "lucide-react"

import type { components } from "@/types/api"

type NotificationType = components["schemas"]["NotificationType"]

/** One icon per notification family — the app's own convention (see statusConfig) is a
 * single restrained treatment rather than a distinct color/icon per fine-grained type. */
const notificationTypeIcons: Record<NotificationType, LucideIcon> = {
  TICKET_ASSIGNED: Ticket,
  TICKET_PRIORITY_CHANGED: Ticket,
  TICKET_STATUS_CHANGED: Ticket,
  TICKET_ARCHIVED: Ticket,
  TICKET_RESTORED: Ticket,
  TICKET_TRANSFERRED: Ticket,
  COMMENT_ADDED: MessageSquare,
  COMMENT_EDITED: MessageSquare,
  COMMENT_DELETED: MessageSquare,
  ATTACHMENT_ADDED: Paperclip,
  ATTACHMENT_DELETED: Paperclip,
  ACCOUNT_ACTIVATED: UserCheck,
  ACCOUNT_DEACTIVATED: UserX,
  ACCOUNT_CREATED: UserCheck,
  NEW_USER_REGISTERED: UserPlus,
  ROLE_ASSIGNED: ShieldCheck,
  ROLE_REVOKED: ShieldCheck,
  PERMISSION_GRANTED: ShieldCheck,
  PERMISSION_REVOKED: ShieldCheck,
  ROLE_PERMISSION_GRANTED: ShieldCheck,
  ROLE_PERMISSION_REVOKED: ShieldCheck,
  // Knowledge base maintenance. Same icon as its Administration nav entry, so a notification
  // about the similarity graph looks like the page it is about; the batch import keeps the
  // upload icon its own panel uses. All three carry no action — nothing to route to.
  SIMILARITY_SCHEDULE_UPDATED: BrainCircuit,
  SIMILARITY_RECALCULATION_FAILED: BrainCircuit,
  BATCH_IMPORT_FAILED: FileUp,
}

export { notificationTypeIcons }
