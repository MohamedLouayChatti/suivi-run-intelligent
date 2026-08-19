import type { components } from "@/types/api"

import { httpClient } from "./client"
import { ApiError } from "./errors"

type SimilarIncident = components["schemas"]["SimilarIncidentResponse"]
type RecalculationSchedule = components["schemas"]["RecalculationScheduleResponse"]
type UpdateRecalculationSchedule = components["schemas"]["UpdateRecalculationScheduleRequest"]
type BatchImportReport = components["schemas"]["BatchImportResponse"]
type BatchImportRejection = components["schemas"]["BatchImportRejectedResponse"]
type TicketImportError = components["schemas"]["TicketImportErrorResponse"]
type Application = components["schemas"]["Application"]

/**
 * GET /knowledge-base/tickets/{id}/similar — the incidents the similarity graph already holds
 * for this ticket, strongest first. Never computed on read: the backend writes them when the
 * ticket is created and refreshes them on every full recalculation, so an empty list means the
 * corpus has nothing close enough, not that a search failed.
 */
async function listSimilarIncidents(ticketId: string): Promise<SimilarIncident[]> {
  const { data } = await httpClient.get<SimilarIncident[]>(
    `/knowledge-base/tickets/${ticketId}/similar`,
  )
  return data
}

async function getRecalculationSchedule(): Promise<RecalculationSchedule> {
  const { data } = await httpClient.get<RecalculationSchedule>("/knowledge-base/recalculation-schedule")
  return data
}

/** PUT, not PATCH: the backend takes the whole schedule, since its fields are meaningless apart. */
async function updateRecalculationSchedule(
  payload: UpdateRecalculationSchedule,
): Promise<RecalculationSchedule> {
  const { data } = await httpClient.put<RecalculationSchedule>(
    "/knowledge-base/recalculation-schedule",
    payload,
  )
  return data
}

/** 202 with no body — the pass outlives the request. 409 when one is already in flight. */
async function runRecalculationNow(): Promise<void> {
  await httpClient.post("/knowledge-base/recalculation/run")
}

async function importTicketBatch(application: Application, file: File): Promise<BatchImportReport> {
  const formData = new FormData()
  formData.append("application", application)
  formData.append("file", file)
  const { data } = await httpClient.post<BatchImportReport>("/knowledge-base/batch-imports", formData)
  return data
}

function hasRejectionShape(body: unknown): body is BatchImportRejection {
  if (typeof body !== "object" || body === null) return false
  const candidate = body as Partial<BatchImportRejection>
  return typeof candidate.total_error_count === "number" && Array.isArray(candidate.errors)
}

/**
 * The per-line report behind a rejected import, or null for any other failure.
 *
 * A rejection is a 422 like FastAPI's own request-validation failures, so the status alone cannot
 * tell them apart — the body is what distinguishes "your file has 37 problems, here they are" from
 * "this request was malformed". Callers use the report when there is one and fall back to the
 * error's own message when there isn't, which is what every other failure of this endpoint (an
 * unreadable file, a file too large, an unreachable knowledge base) already carries.
 */
function asImportRejection(error: unknown): BatchImportRejection | null {
  if (!(error instanceof ApiError) || error.status !== 422) return null
  return hasRejectionShape(error.body) ? error.body : null
}

export {
  listSimilarIncidents,
  getRecalculationSchedule,
  updateRecalculationSchedule,
  runRecalculationNow,
  importTicketBatch,
  asImportRejection,
}
export type {
  SimilarIncident,
  RecalculationSchedule,
  UpdateRecalculationSchedule,
  BatchImportReport,
  BatchImportRejection,
  TicketImportError,
}
