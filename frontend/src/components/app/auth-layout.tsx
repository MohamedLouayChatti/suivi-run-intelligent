import Link from "next/link";
import Image from "next/image";

interface AuthLayoutProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function AuthLayout({ title, description, children }: AuthLayoutProps) {
  return (
    <div className="grid flex-1 lg:grid-cols-5">
      <div className="flex flex-1 flex-col px-8 py-10 sm:px-12 lg:col-span-2 lg:px-16">
        <Link href="/login" className="flex items-center gap-2.5">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary text-[13px] font-semibold text-primary-foreground">
            SR
          </div>
          <span className="text-[15px] font-semibold tracking-tight">
            Suivi Run
          </span>
        </Link>

        <div className="flex flex-1 flex-col items-center justify-center">
          <div className="w-full max-w-sm">
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
        <Image
          src="/wide_sofrecom_logo.png"
          alt="Logo Sofrecom"
          width={600}
          height={152}
          className="h-auto w-[min(75%,360px)] max-w-full"
          priority
        />
      </div>
    </div>
  );
}

export { AuthLayout };
