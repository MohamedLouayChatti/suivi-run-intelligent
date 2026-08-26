import { frFR } from "@clerk/localizations";

const FALLBACK_MESSAGE = "Une erreur est survenue. Veuillez réessayer.";

// Clerk's own French translations for its error codes (the same catalog `ClerkProvider`'s
// `localization` prop uses for its hosted components) — reused here so a custom-flow error
// gets the official French wording instead of the English `message`/`longMessage` the Frontend
// API returns. Not every code has a translation (some entries are `undefined` in the catalog),
// so an unmapped code still falls back to Clerk's own message.
const unstableErrors = frFR.unstable__errors as Record<string, string | undefined>;

/**
 * Structural (not imported) type: Clerk's Core 3 custom-flow methods resolve to
 * `{ error: ClerkError | null }` instead of throwing, and `ClerkError` isn't part of
 * `@clerk/nextjs`'s/`@clerk/react`'s public export surface — matching its shape here avoids
 * depending on `@clerk/shared`, which this app never installs directly.
 */
interface ClerkOperationError {
  code?: string;
  message: string;
  longMessage?: string;
}

function clerkErrorMessage(error: ClerkOperationError | null | undefined): string {
  if (!error) return FALLBACK_MESSAGE;
  const translated = error.code ? unstableErrors[error.code] : undefined;
  return translated ?? error.longMessage ?? error.message ?? FALLBACK_MESSAGE;
}

/**
 * User resource methods (`user.update`, `user.updatePassword`, ...) don't follow the Core 3
 * `{ error }` return shape above — they throw a `ClerkAPIResponseError` whose `errors` array
 * carries the same `{ code, message, longMessage }` shape. Structural here for the same reason as
 * `ClerkOperationError`: avoids depending on `@clerk/shared` just for `isClerkAPIResponseError`.
 */
function clerkThrownErrorMessage(error: unknown): string {
  const errors = (error as { errors?: ClerkOperationError[] } | null)?.errors;
  return clerkErrorMessage(errors?.[0]);
}

export { clerkErrorMessage, clerkThrownErrorMessage };
