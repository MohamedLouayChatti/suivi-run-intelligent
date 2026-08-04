import Link from "next/link";
import Image from "next/image";
import { Compass } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 text-center">
      <Link href="/" className="flex items-center gap-2.5">
        <Image
          src="/icon_sofrecom_logo.png"
          alt="Logo Sofrecom"
          width={139}
          height={150}
          priority
          className="h-8 w-auto shrink-0 object-contain group-data-[collapsible=icon]:h-6"
        />
        <span className="text-[15px] font-semibold tracking-tight">
          Suivi Run
        </span>
      </Link>

      <div className="flex flex-col items-center gap-3">
        <Compass className="size-8 text-muted-foreground" />
        <h1 className="text-lg font-semibold text-foreground">
          404 — Page introuvable
        </h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          La page que vous recherchez n&apos;existe pas ou a été déplacée.
        </p>
        <Button asChild size="sm" className="mt-2">
          <Link href="/">Retour à l&apos;accueil</Link>
        </Button>
      </div>
    </div>
  );
}
