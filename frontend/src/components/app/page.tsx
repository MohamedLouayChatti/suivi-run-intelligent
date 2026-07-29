import Link from "next/link"
import { ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
} from "@/components/ui/card"

interface Breadcrumb {
  label: string
  href?: string
}

interface PageHeaderProps {
  title: string
  description?: React.ReactNode
  breadcrumbs?: Breadcrumb[]
  actions?: React.ReactNode
}

function PageHeader({ title, description, breadcrumbs, actions }: PageHeaderProps) {
  return (
    <div className="border-b border-border bg-background">
      <div className="mx-auto max-w-[112rem] px-4 py-5 md:px-8">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="mb-2 flex items-center gap-1 text-xs text-muted-foreground">
            {breadcrumbs.map((b, i) => (
              <span key={b.label} className="flex items-center gap-1">
                {i > 0 && <ChevronRight className="size-3" />}
                {b.href ? (
                  <Link href={b.href} className="transition-colors hover:text-foreground">
                    {b.label}
                  </Link>
                ) : (
                  <span className="text-foreground">{b.label}</span>
                )}
              </span>
            ))}
          </nav>
        )}
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4 sm:flex sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold">{title}</h1>
            {description && (
              <div className="mt-1 text-sm text-muted-foreground">{description}</div>
            )}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      </div>
    </div>
  )
}

interface PageBodyProps {
  children: React.ReactNode
  className?: string
}

function PageBody({ children, className }: PageBodyProps) {
  return (
    <div className="flex-1">
      <div className={cn("mx-auto max-w-[112rem] px-4 py-6 md:px-8", className)}>{children}</div>
    </div>
  )
}

interface SectionCardProps {
  title?: React.ReactNode
  description?: React.ReactNode
  action?: React.ReactNode
  className?: string
  bodyClassName?: string
  children: React.ReactNode
}

function SectionCard({
  title,
  description,
  action,
  className,
  bodyClassName,
  children,
}: SectionCardProps) {
  return (
    <Card className={className}>
      {(title || description || action) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
          {action && <CardAction>{action}</CardAction>}
        </CardHeader>
      )}
      <CardContent className={bodyClassName}>{children}</CardContent>
    </Card>
  )
}

export { PageHeader, PageBody, SectionCard }
