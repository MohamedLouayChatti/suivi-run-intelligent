import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Next.js 16 renamed the network-boundary file from middleware.ts to proxy.ts;
// clerkMiddleware itself is unchanged.
//
// Edge-level responsibility ends at "does a Clerk session exist" — it must never
// call /auth/me or reason about roles/permissions/applications. auth.protect()
// redirects unauthenticated requests to NEXT_PUBLIC_CLERK_SIGN_IN_URL (/login);
// everything past that point is decided client-side once GET /auth/me resolves.
const isPublicRoute = createRouteMatcher([
  "/login(.*)",
  "/signup(.*)",
  "/forgot-password(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
