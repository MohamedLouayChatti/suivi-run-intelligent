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
  /**
   * The backend's own `detail` when it is a type name (`"TicketNotFound"`,
   * `"BatchImportCorpusWriteFailed"`, …) — every domain/application error answers with one.
   * Stable across wording changes, so it is what feature code should branch on rather than
   * matching on `message`.
   */
  readonly code: string | null;
  /**
   * The raw response body, kept so a feature can read the extra fields its own endpoint
   * returns. Almost every error in this API is `{ detail }` and nothing more; the batch
   * import's rejection is the one that carries a whole per-line report, and throwing it
   * away here would mean the shared client deciding which endpoints are allowed to
   * explain themselves.
   */
  readonly body: unknown;

  constructor(
    message: string,
    status: number | null,
    issues: ApiValidationIssue[] = [],
    code: string | null = null,
    body: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.issues = issues;
    this.code = code;
    this.body = body;
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

/**
 * Backend error bodies are `{ detail: string }`, FastAPI's 422 `{ detail: ValidationError[] }`,
 * or — for the handful of errors whose reader has to act on the specifics — `{ detail, message }`
 * with a written sentence alongside the type name.
 */
interface BackendErrorBody {
  detail?: string | unknown[];
  message?: string;
}

function normalizeApiError(error: AxiosError<BackendErrorBody>): ApiError {
  if (!error.response) {
    return new ApiError("Connexion impossible. Vérifiez votre réseau.", null);
  }

  const { status, data } = error.response;
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    return new ApiError("Requête invalide.", status, extractValidationIssues(detail), null, data);
  }

  const code = typeof detail === "string" ? detail : null;
  // `message` first when the backend wrote one: it is a sentence meant for the person reading it,
  // where `detail` is only ever the exception's class name. Falling back to the type name keeps
  // every other error exactly as it behaved before. `error.message` is Axios's own English
  // sentence ("Request failed with status code 500") and is never shown to the user — a response
  // this shapeless (no `detail` at all) gets the same generic French fallback as no response.
  const message = data?.message ?? code ?? "Une erreur est survenue. Veuillez réessayer.";

  return new ApiError(message, status, [], code, data);
}

export { ApiError, normalizeApiError };
export type { ApiValidationIssue, BackendErrorBody };
