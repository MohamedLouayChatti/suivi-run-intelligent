import { ShieldAlert } from "lucide-react";

/**
 * Rendered instead of a page's content when the current user can reach the route but is known
 * to lack access to it — never a redirect, so the URL and the reason both stay visible.
 */
function AccessDeniedScreen() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
      <ShieldAlert className="size-8 text-muted-foreground" />
      <h1 className="text-lg font-semibold text-foreground">Accès refusé</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        Vous n&apos;avez pas les droits nécessaires pour accéder à cette page.
      </p>
    </div>
  );
}

export { AccessDeniedScreen };
