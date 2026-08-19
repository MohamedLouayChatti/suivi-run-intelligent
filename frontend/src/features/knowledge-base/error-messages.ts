import { ApiError } from "@/services/api/errors"

/**
 * French wording for the Knowledge Base failures the backend answers with a type name alone.
 *
 * Most of this module's errors carry a written sentence, which `ApiError.message` already holds
 * and which is the text to show — it is the backend's own explanation, and it says what to do
 * next. The exceptions are the errors translated by the generic handler, whose whole body is
 * `{ detail: "<TypeName>" }`; there is no sentence to show, so one is written here. Keyed on
 * `ApiError.code` rather than on the message, since the code is the stable half.
 */
const messagesByCode: Record<string, string> = {
  RecalculationAlreadyRunning:
    "Un recalcul complet du graphe de similarité est déjà en cours. Attendez qu'il se termine avant de relancer une passe ou de déposer un fichier.",
}

/** The sentence to show for a failed Knowledge Base request. */
function describeKnowledgeBaseError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "Une erreur inattendue est survenue. Réessayez."
  }
  if (error.code && messagesByCode[error.code]) {
    return messagesByCode[error.code]
  }
  if (error.status === 403) {
    return "Vous n'avez pas les permissions nécessaires pour cette action."
  }
  // Either the backend's own sentence, or its exception name when it wrote none — the second
  // reads as a defect, which is exactly what an unmapped code without a message is.
  return error.message
}

export { describeKnowledgeBaseError }
