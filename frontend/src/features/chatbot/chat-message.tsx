"use client"

import { useState } from "react"
import { Check, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { ChatMessage as ChatMessageType } from "@/features/chatbot/types"

interface ChatMessageProps {
  message: ChatMessageType
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

function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [copyFailed, setCopyFailed] = useState(false)

  async function handleCopy() {
    if (!message.content.trim()) return

    try {
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
        <p className="max-w-[42rem] rounded-lg rounded-tr-sm bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground">
          {message.content}
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-4">
      <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-primary text-[11px] font-semibold text-primary-foreground">
        SR
      </span>
      <div className="min-w-0 max-w-[48rem] flex-1">
        <div className="space-y-3 text-sm leading-relaxed text-foreground">
          {message.content.split("\n\n").map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>

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
      </div>
    </div>
  )
}

export { ChatMessage }
