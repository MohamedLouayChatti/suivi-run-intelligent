import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/services/api/errors";

function isNonRetryableStatus(status: number | null): boolean {
  return status !== null && status >= 400 && status < 500;
}

/**
 * The app's server-state defaults. Retries back off on client errors (4xx) —
 * a bad request or missing permission won't succeed on retry — but allow a
 * couple of retries on network/5xx failures.
 */
function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        // On, and deliberately: with it off, a tab left open showed data of
        // unbounded age and nothing anywhere dislodged it — the 60s stale time
        // only decides whether a refetch is *needed*, never that one happens.
        // Returning to a tab is the cheapest honest moment to catch up on
        // everything that changed while it was in the background.
        refetchOnWindowFocus: true,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && isNonRetryableStatus(error.status)) {
            return false;
          }
          return failureCount < 2;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export { createQueryClient };
