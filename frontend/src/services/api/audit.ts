import type { components } from "@/types/api"

import { httpClient } from "./client"

type AuditEntry = components["schemas"]["AuditEntryResponse"]
type PagedAuditEntries = components["schemas"]["PagedResponse_AuditEntryResponse_"]

interface ListAuditEntriesQuery {
  module: "all" | string
  page: number
  pageSize: number
}

/**
 * Server-side filtered (by module) and paginated. The audit log's free-text search box stays
 * a client-side refinement over whatever page this returns (see audit-log-table.tsx) — it
 * matches actor display name, which only exists after a separate cross-module lookup into
 * Auth's user directory, so it has no single-query server-side equivalent the way `module` does.
 */
async function listAuditEntries({ module, page, pageSize }: ListAuditEntriesQuery): Promise<PagedAuditEntries> {
  const { data } = await httpClient.get<PagedAuditEntries>("/audit", {
    params: { module: module === "all" ? undefined : module, page, page_size: pageSize },
  })
  return data
}

interface AuditExportFilters {
  module: string | "all"
}

/** Exports the Audit page's currently active module filter as a CSV, matching what's on screen. */
async function exportAuditEntries(filters: AuditExportFilters): Promise<Blob> {
  const { data } = await httpClient.get<Blob>("/audit/export", {
    responseType: "blob",
    params: {
      module: filters.module === "all" ? undefined : filters.module,
    },
  })
  return data
}

export { listAuditEntries, exportAuditEntries }
export type { AuditEntry }
