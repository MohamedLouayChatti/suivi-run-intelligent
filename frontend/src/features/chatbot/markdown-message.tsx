"use client"

import type { ComponentPropsWithoutRef } from "react"
import ReactMarkdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"

/**
 * Renders an assistant answer as Markdown. The system prompt tells the model to write Markdown
 * and it does — headings, bold, bullet and numbered lists — so anything short of a real parser
 * put the raw `###` and `**` in front of the reader.
 *
 * No `rehype-raw`: react-markdown ignores embedded HTML by default, and it stays that way here.
 * A model answer can quote a ticket description verbatim, so its text is untrusted content that
 * must never become markup.
 *
 * Every element is styled explicitly rather than through a typography preset — this project has
 * no `@tailwindcss/typography` — which also keeps the bubble's own rhythm (`text-sm`, tight
 * spacing) instead of an article's.
 */

const components: Components = {
  h1: ({ children }) => <h3 className="mt-5 mb-2 text-base font-semibold first:mt-0">{children}</h3>,
  h2: ({ children }) => <h3 className="mt-5 mb-2 text-base font-semibold first:mt-0">{children}</h3>,
  h3: ({ children }) => <h4 className="mt-4 mb-1.5 text-sm font-semibold first:mt-0">{children}</h4>,
  h4: ({ children }) => <h5 className="mt-4 mb-1.5 text-sm font-semibold first:mt-0">{children}</h5>,
  h5: ({ children }) => <h6 className="mt-4 mb-1.5 text-sm font-semibold first:mt-0">{children}</h6>,
  h6: ({ children }) => <h6 className="mt-4 mb-1.5 text-sm font-semibold first:mt-0">{children}</h6>,
  p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5 first:mt-0 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5 first:mt-0 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5 marker:text-muted-foreground">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-border pl-3 text-muted-foreground">{children}</blockquote>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="text-primary underline underline-offset-2 hover:no-underline"
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-4 border-border" />,
  // Fenced blocks arrive as <pre><code>; `pre` owns the scroll box so a long line scrolls inside
  // the bubble instead of widening the whole chat column.
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-md border border-border bg-surface p-3 text-xs first:mt-0 last:mb-0">
      {children}
    </pre>
  ),
  code: ({ children, className, ...props }: ComponentPropsWithoutRef<"code">) =>
    // A fenced block's <code> carries a `language-*` class and is already inside a styled <pre>;
    // an inline span carries none and gets its own chip.
    className ? (
      <code className={`${className} font-mono`} {...props}>
        {children}
      </code>
    ) : (
      <code className="rounded bg-surface px-1 py-0.5 font-mono text-[0.85em]" {...props}>
        {children}
      </code>
    ),
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto first:mt-0 last:mb-0">
      <table className="w-full border-collapse text-left text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-border">{children}</thead>,
  th: ({ children }) => <th className="px-2 py-1.5 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-t border-border px-2 py-1.5 align-top">{children}</td>,
}

function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="text-sm leading-relaxed text-foreground">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

export { MarkdownMessage }
