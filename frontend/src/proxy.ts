import { clerkMiddleware } from "@clerk/nextjs/server";

// Next.js 16 renamed the network-boundary file from middleware.ts to proxy.ts;
// clerkMiddleware itself is unchanged.
//
// Session protection is no longer done here via createRouteMatcher path-matching
// (deprecated by Clerk — see https://clerk.com/docs/guides/development/upgrading/upgrade-guides/migrate-from-create-route-matcher).
// Each protected resource now calls auth.protect() itself — see app/(protected)/layout.tsx,
// which gates the whole route group. auth.protect() redirects unauthenticated requests to
// NEXT_PUBLIC_CLERK_SIGN_IN_URL (/login); everything past that point is decided client-side
// once GET /auth/me resolves.
export default clerkMiddleware();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
