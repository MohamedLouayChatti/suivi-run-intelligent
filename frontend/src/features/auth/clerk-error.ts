import { isClerkAPIResponseError } from "@clerk/nextjs/errors";

const FALLBACK_MESSAGE = "Une erreur est survenue. Veuillez réessayer.";

function getClerkErrorMessage(error: unknown): string {
  if (isClerkAPIResponseError(error)) {
    return error.errors[0]?.longMessage ?? error.errors[0]?.message ?? FALLBACK_MESSAGE;
  }
  return FALLBACK_MESSAGE;
}

export { getClerkErrorMessage };
