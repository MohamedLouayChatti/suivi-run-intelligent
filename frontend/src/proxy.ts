import { clerkMiddleware } from "@clerk/nextjs/server";

// Next.js 16 renamed the network-boundary file from middleware.ts to proxy.ts;
// clerkMiddleware itself is unchanged. This only attaches auth state to each
// request — no route protection (auth().protect()) is wired up yet.
export default clerkMiddleware();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
