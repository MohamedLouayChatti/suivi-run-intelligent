import Link from "next/link";

interface AuthLayoutProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function AuthLayout({ title, description, children }: AuthLayoutProps) {
  return (
    <div className="grid flex-1 lg:grid-cols-5">
      <div className="flex flex-col justify-between px-8 py-10 sm:px-12 lg:col-span-2 lg:px-16">
        <div>
          <Link href="/login" className="flex items-center gap-2.5">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary text-[13px] font-semibold text-primary-foreground">
              SR
            </div>
            <span className="text-[15px] font-semibold tracking-tight">
              Suivi Run
            </span>
          </Link>

          <div className="mt-12 w-full max-w-sm lg:mt-16">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {title}
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {description}
            </p>
            <div className="mt-8">{children}</div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Plateforme interne · Les accès sont journalisés et audités.
        </p>
      </div>

      <div className="hidden border-l border-border bg-surface lg:col-span-3 lg:flex lg:items-center lg:justify-center">
        <div className="flex size-40 items-center justify-center rounded-2xl border border-dashed border-border text-center text-sm text-muted-foreground">
          Logo de l&apos;entreprise
        </div>
      </div>
    </div>
  );
}

export { AuthLayout };
