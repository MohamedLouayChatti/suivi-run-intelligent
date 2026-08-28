"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { ArrowUpRight } from "lucide-react"

interface ResourceReferenceLinkProps {
  href: string
  children: ReactNode
}

/**
 * An inline reference to something inside the application, rendered the way a citation is: the
 * words stay part of the sentence and only a dotted underline marks them as reachable, so a
 * paragraph naming six tickets still reads as prose rather than as a list of buttons. Colour is
 * held back for hover, which is what distinguishes this from an ordinary link — the reader is
 * told the text is a destination without being urged toward it.
 *
 * `ArrowUpRight` is the same affordance the Dashboard shortcuts and the similar-incidents card
 * already use for "this opens elsewhere". `whitespace-nowrap` on the icon keeps it from wrapping
 * alone onto the next line, orphaned from the last word of the label.
 */
function ResourceReferenceLink({ href, children }: ResourceReferenceLinkProps) {
  return (
    <Link
      href={href}
      className="font-medium text-foreground underline decoration-muted-foreground/50 decoration-dotted underline-offset-[3px] transition-colors hover:text-primary hover:decoration-primary focus-visible:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:rounded-sm"
    >
      {children}
      <ArrowUpRight className="ml-0.5 inline size-3 shrink-0 -translate-y-px whitespace-nowrap opacity-60" />
    </Link>
  )
}

export { ResourceReferenceLink }
