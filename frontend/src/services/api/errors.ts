import type { AxiosError } from "axios";

/** One field-level validation failure, normalized from FastAPI's 422 detail array. */
interface ApiValidationIssue {
  field: string;
  message: string;
}

/**
 * Normalized shape every backend failure is converted into, so feature code never
 * has to know it's talking to Axios or to a FastAPI-shaped error response.
 */
class ApiError extends Error {
  readonly status: number | null;
  readonly issues: ApiValidationIssue[];

  constructor(message: string, status: number | null, issues: ApiValidationIssue[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.issues = issues;
  }
}

interface FastApiValidationDetailEntry {
  loc: (string | number)[];
  msg: string;
}

function isValidationDetailEntry(entry: unknown): entry is FastApiValidationDetailEntry {
  return (
    typeof entry === "object" &&
    entry !== null &&
    "loc" in entry &&
    "msg" in entry &&
    typeof (entry as { msg: unknown }).msg === "string"
  );
}

function extractValidationIssues(detail: unknown): ApiValidationIssue[] {
  if (!Array.isArray(detail)) {
    return [];
  }
  return detail.filter(isValidationDetailEntry).map((entry) => ({
    field: entry.loc.filter((part) => typeof part === "string").join("."),
    message: entry.msg,
  }));
}

/** Backend error bodies are either `{ detail: string }` or FastAPI's 422 `{ detail: ValidationError[] }`. */
interface BackendErrorBody {
  detail?: string | unknown[];
}

function normalizeApiError(error: AxiosError<BackendErrorBody>): ApiError {
  if (!error.response) {
    return new ApiError("Network error. Please check your connection.", null);
  }

  const { status, data } = error.response;
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    return new ApiError("Validation failed.", status, extractValidationIssues(detail));
  }

  return new ApiError(typeof detail === "string" ? detail : error.message, status);
}

export { ApiError, normalizeApiError };
export type { ApiValidationIssue, BackendErrorBody };
