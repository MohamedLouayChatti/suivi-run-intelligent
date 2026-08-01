import { auth } from "@clerk/nextjs/server";

import { ProtectedShell } from "./protected-shell";

/**
 * Server-side resource check: every route under this group requires a Clerk session.
 * Resource-based per-route/layout auth.protect() replaces the old middleware
 * createRouteMatcher + auth.protect() pattern (see proxy.ts) — Clerk deprecated the
 * latter because path matching in middleware can drift from the app's real route
 * structure and leave a protected resource reachable.
 */
export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await auth.protect();

  return <ProtectedShell>{children}</ProtectedShell>;
}
