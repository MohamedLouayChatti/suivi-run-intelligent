"use client";

import { useAuth, useUser } from "@clerk/nextjs";

/**
 * The rest of the app's view of authentication state — hides Clerk's hooks/types
 * so presentation and feature code depend on this abstraction instead of Clerk directly.
 */
interface AuthSession {
  isLoaded: boolean;
  isSignedIn: boolean;
  userId: string | null;
  email: string | null;
  imageUrl: string | null;
  setProfileImage: (file: File) => Promise<void>;
}

function useAuthSession(): AuthSession {
  const { isLoaded, isSignedIn, userId } = useAuth();
  const { user } = useUser();

  return {
    isLoaded,
    isSignedIn: isSignedIn ?? false,
    userId: userId ?? null,
    email: user?.primaryEmailAddress?.emailAddress ?? null,
    imageUrl: user?.imageUrl ?? null,
    setProfileImage: async (file: File) => {
      if (!user) return;
      await user.setProfileImage({ file });
    },
  };
}

export { useAuthSession };
export type { AuthSession };
