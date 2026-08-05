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

export { clerkErrorMessage };
