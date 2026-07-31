/**
 * Module-level bridge between Clerk (React-hook-only token access) and
 * non-component code such as the shared Axios client, which needs to read
 * the current JWT outside of the React render tree.
 *
 * AuthTokenBridge (a client component mounted once near the app root)
 * registers Clerk's `getToken` here; everything else only calls `getAuthToken`.
 */

type TokenGetter = () => Promise<string | null>;

let currentTokenGetter: TokenGetter = async () => null;

function registerAuthTokenGetter(getter: TokenGetter): void {
  currentTokenGetter = getter;
}

async function getAuthToken(): Promise<string | null> {
  return currentTokenGetter();
}

export { registerAuthTokenGetter, getAuthToken };
export type { TokenGetter };
