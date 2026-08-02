"use client";

import type { ReactNode } from "react";
import { Loader2, ServerCrash, ShieldAlert, UserX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/services/api/errors";

import { useAuthSession } from "./use-auth-session";
import { useCurrentUser } from "./use-current-user";
import { useLogout } from "./use-logout";

interface AuthStateScreenProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

function AuthStateScreen({ icon, title, description, action }: AuthStateScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
      {icon}
      <h1 className="text-lg font-semibold text-foreground">{title}</h1>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}

function LoadingScreen() {
  return (
    <AuthStateScreen
      icon={<Loader2 className="size-6 animate-spin text-muted-foreground" />}
      title="Initialisation…"
      description="Vérification de votre session."
    />
  );
}

/**
 * Gates every protected route behind application bootstrap: Clerk session ->
 * JWT -> GET /auth/me -> cached current user. Nothing under (protected) renders
 * until identity is confirmed — the edge (proxy.ts) only checked that a Clerk
 * session exists, so a signed-in-but-unrecognized user must still be caught here.
 *
 * 401s are handled globally by the auth-failure bridge (sign-out + cache clear +
 * redirect to /login); this just keeps showing the loading state while that's
 * in flight instead of flashing a generic error first.
 */
function AuthGate({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuthSession();
  const query = useCurrentUser();
  const logout = useLogout();

  if (!isLoaded || !isSignedIn || query.isPending) {
    return <LoadingScreen />;
  }

  if (query.isError) {
    const status = query.error instanceof ApiError ? query.error.status : null;

    if (status === 401) {
      return <LoadingScreen />;
    }

    if (status === 403) {
      return (
        <AuthStateScreen
          icon={<ShieldAlert className="size-8 text-muted-foreground" />}
          title="Accès refusé"
          description="Votre compte n'est pas autorisé à accéder à cette application."
          action={
            <Button size="sm" variant="outline" onClick={() => void logout()}>
              Se déconnecter
            </Button>
          }
        />
      );
    }

    if (status === 404) {
      return (
        <AuthStateScreen
          icon={<UserX className="size-8 text-muted-foreground" />}
          title="Compte introuvable"
          description="Aucun compte applicatif n'est associé à votre session. Contactez un administrateur."
          action={
            <Button size="sm" variant="outline" onClick={() => void logout()}>
              Se déconnecter
            </Button>
          }
        />
      );
    }

    return (
      <AuthStateScreen
        icon={<ServerCrash className="size-8 text-muted-foreground" />}
        title="Une erreur est survenue"
        description="Impossible de contacter le serveur. Veuillez réessayer."
        action={
          <Button size="sm" onClick={() => query.refetch()}>
            Réessayer
          </Button>
        }
      />
    );
  }

  return <>{children}</>;
}

export { AuthGate };
