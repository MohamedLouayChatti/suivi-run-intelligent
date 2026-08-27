"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown, Copy, Check } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ChatMessage as ChatMessageType } from "@/features/chatbot/types"

interface ChatMessageProps {
  message: ChatMessageType
}

function ChatMessage({ message }: ChatMessageProps) {
  const [feedback, setFeedback] = useState<"helpful" | "not-helpful" | null>(null)
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
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
            className={cn(feedback === "helpful" && "text-primary")}
            onClick={() => setFeedback("helpful")}
          >
            <ThumbsUp className="size-3.5" /> Utile
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={cn(feedback === "not-helpful" && "text-primary")}
            onClick={() => setFeedback("not-helpful")}
          >
            <ThumbsDown className="size-3.5" /> Pas utile
          </Button>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
            {copied ? "Copié" : "Copier"}
          </Button>
        </div>
      </div>
    </div>
  )
}

export { ChatMessage }
