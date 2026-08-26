const FALLBACK_MESSAGE = "Une erreur est survenue. Veuillez réessayer.";

/**
 * Structural (not imported) type: Clerk's Core 3 custom-flow methods resolve to
 * `{ error: ClerkError | null }` instead of throwing, and `ClerkError` isn't part of
 * `@clerk/nextjs`'s/`@clerk/react`'s public export surface — matching its shape here avoids
 * depending on `@clerk/shared`, which this app never installs directly.
 */
interface ClerkOperationError {
  message: string;
  longMessage?: string;
}

function clerkErrorMessage(error: ClerkOperationError | null | undefined): string {
  if (!error) return FALLBACK_MESSAGE;
  return error.longMessage ?? error.message ?? FALLBACK_MESSAGE;
}

/**
 * User resource methods (`user.update`, `user.updatePassword`, ...) don't follow the Core 3
 * `{ error }` return shape above — they throw a `ClerkAPIResponseError` whose `errors` array
 * carries the same `{ message, longMessage }` shape. Structural here for the same reason as
 * `ClerkOperationError`: avoids depending on `@clerk/shared` just for `isClerkAPIResponseError`.
 */
function clerkThrownErrorMessage(error: unknown): string {
  const errors = (error as { errors?: ClerkOperationError[] } | null)?.errors;
  return clerkErrorMessage(errors?.[0]);
}

export { clerkErrorMessage, clerkThrownErrorMessage };
