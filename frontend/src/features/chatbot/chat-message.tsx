"use client"

import { useState } from "react"
import { AlertCircle, Bot, Check, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"
import { MarkdownMessage } from "@/features/chatbot/markdown-message"
import type { ChatMessage as ChatMessageType } from "@/features/chatbot/types"

interface ChatMessageProps {
  message: ChatMessageType
  // True only for the still-empty assistant bubble waiting on its first streamed delta — see
  // ChatPanel. Shows a "thinking" indicator in place of the (otherwise blank) answer area.
  isPending?: boolean
}

async function copyToClipboard(content: string) {
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(content)
      return
    }
  } catch {
    // Some browsers expose the Clipboard API but reject it because of a permission policy.
    // Fall back to the legacy copy command in that case.
  }

  const textarea = document.createElement("textarea")
  textarea.value = content
  textarea.setAttribute("readonly", "")
  textarea.style.position = "fixed"
  textarea.style.opacity = "0"
  document.body.appendChild(textarea)
  textarea.select()

  const copied = document.execCommand("copy")
  textarea.remove()

  if (!copied) throw new Error("Clipboard unavailable")
}

function ChatMessage({ message, isPending = false }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [copyFailed, setCopyFailed] = useState(false)

  async function handleCopy() {
    if (!message.content.trim()) return

    try {
      // The Markdown source, not the rendered text: it is what the user can paste back into a
      // ticket comment or another chat and get the same formatting from.
      await copyToClipboard(message.content)
      setCopied(true)
      setCopyFailed(false)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopyFailed(true)
      setTimeout(() => setCopyFailed(false), 3000)
    }
  }

  if (message.role === "USER") {
    return (
      <div className="flex justify-end gap-4">
        <p className="max-w-[42rem] rounded-lg rounded-tr-sm bg-primary px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-primary-foreground">
          {message.content}
        </p>
      </div>
    )
  }

  // A run that never produced an answer. Deliberately not rendered as Markdown and not given the
  // copy action: there is nothing here the reader would paste into a ticket, and dressing a
  // failure up as an ordinary reply is what let it pass unnoticed in the transcript.
  if (message.failed) {
    return (
      <div className="flex gap-4">
        <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md border border-destructive/30 bg-destructive/10 text-destructive">
          <AlertCircle className="size-4" strokeWidth={1.75} />
        </span>
        <p className="min-w-0 max-w-[48rem] flex-1 self-center text-sm leading-relaxed text-muted-foreground">
          {message.content}
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-4">
      <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground">
        <Bot className="size-4" strokeWidth={1.75} />
      </span>
      <div className="min-w-0 max-w-[48rem] flex-1">
        {isPending ? (
          <div
            className="flex h-7 items-center gap-1.5"
            role="status"
            aria-label="L'assistant rédige une réponse"
          >
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.3s]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.15s]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50" />
          </div>
        ) : (
          <>
            <MarkdownMessage content={message.content} />

            <div className="mt-3 flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                disabled={!message.content.trim()}
                aria-live="polite"
              >
                {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                {copied ? "Copié" : copyFailed ? "Copie impossible" : "Copier"}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export { ChatMessage }
