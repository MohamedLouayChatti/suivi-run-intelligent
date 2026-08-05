import type { components } from "@/types/api"

import { httpClient } from "./client"

type AuditEntry = components["schemas"]["AuditEntryResponse"]

/**
 * Mirrors listTickets/listUsers: fetch one large page from the backend, filter/search/
 * paginate client-side (see audit-log-table.tsx) rather than round-tripping per filter
 * change — same convention used everywhere else in this app.
 */
async function listAuditEntries(pageSize = 100): Promise<AuditEntry[]> {
  const { data } = await httpClient.get<AuditEntry[]>("/audit", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

export { listAuditEntries }
export type { AuditEntry }
