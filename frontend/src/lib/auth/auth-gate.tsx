"use client";

import type { ReactNode } from "react";
import { Loader2, ServerCrash, ShieldAlert, UserX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/services/api/errors";
import { useCooldown } from "@/hooks/use-cooldown";

import { useAuthSession } from "./use-auth-session";
import { useCurrentUser } from "./use-current-user";
import { useLogout } from "./use-logout";

/**
 * How long the manual "Réessayer" stays disabled after a press.
 *
 * A debounce rather than a real rate limit, and chosen as one: /auth/me is a single
 * indexed lookup, the screen behind it is one nobody sits on for long, and the point is
 * to stop a frustrated user hammering the button — not to ration a scarce resource. The
 * 30s automatic poll is what bounds the steady-state load; this only bounds the bursts.
 */
const RETRY_COOLDOWN_MS = 5_000;

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

interface DeactivatedScreenProps {
  onRetry: () => void;
  isChecking: boolean;
  onLogout: () => void;
}

/**
 * What a user whose account is not active sees, and the only screen in the app that can
 * replace itself with the application without anyone navigating.
 *
 * Its own component rather than a branch inside AuthGate because it holds cooldown
 * state, and a hook cannot be called from inside a conditional. Signing out was the only
 * thing offered here before, which is the wrong shape for the situation: the user is
 * waiting on someone else, not stuck. `useCurrentUser` re-checks every 30s on its own,
 * and this button is for the case where they have just been told they were activated and
 * would rather not wait out the interval.
 */
function DeactivatedScreen({ onRetry, isChecking, onLogout }: DeactivatedScreenProps) {
  const cooldown = useCooldown(RETRY_COOLDOWN_MS);

  function handleRetry() {
    cooldown.start();
    onRetry();
  }

  return (
    <AuthStateScreen
      icon={<ShieldAlert className="size-8 text-muted-foreground" />}
      title="Accès refusé"
      description="Votre compte n'est pas autorisé à accéder à cette application. Cette page se met à jour automatiquement dès qu'un administrateur l'active."
      action={
        <div className="flex items-center gap-2">
          <Button size="sm" onClick={handleRetry} disabled={isChecking || cooldown.isCoolingDown}>
            {isChecking
              ? "Vérification…"
              : cooldown.isCoolingDown
                ? `Réessayer (${cooldown.remainingSeconds}s)`
                : "Réessayer"}
          </Button>
          <Button size="sm" variant="outline" onClick={onLogout}>
            Se déconnecter
          </Button>
        </div>
      }
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
        <DeactivatedScreen
          onRetry={() => void query.refetch()}
          isChecking={query.isFetching}
          onLogout={() => void logout()}
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
