"use client"

import { useEffect, useRef, useState } from "react"
import { Send, BookOpen, CornerDownLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ChatMessage } from "@/features/chatbot/chat-message"
import { suggestedPrompts, type ChatMessage as ChatMessageType } from "@/features/chatbot/mock-data"

interface ChatPanelProps {
  messages: ChatMessageType[]
  isStreaming: boolean
  onSend: (content: string) => void
}

function ChatPanel({ messages, isStreaming, onSend }: ChatPanelProps) {
  const [input, setInput] = useState("")
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isStreaming])

  function handleSend(content: string) {
    if (!content.trim() || isStreaming) return
    onSend(content)
    setInput("")
    inputRef.current?.focus()
  }

  return (
    <div className="flex min-w-0 flex-col rounded-lg border border-border bg-card">
      <div className="min-h-[26rem] flex-1 space-y-8 overflow-y-auto p-6">
        {messages.length === 0 && (
          <div className="mx-auto max-w-xl py-10 text-center">
            <div className="mx-auto grid size-11 place-items-center rounded-lg border border-border bg-surface">
              <BookOpen className="size-5 text-primary" strokeWidth={1.5} />
            </div>
            <h2 className="mt-4 text-sm font-semibold">
              Posez une question sur un incident, un runbook ou un ticket
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              L&apos;assistant répond uniquement à partir des sources internes indexées et cite
              toujours ses sources.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isStreaming && (
          <div className="flex gap-4">
            <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-primary text-[11px] font-semibold text-primary-foreground">
              SR
            </span>
            <p className="animate-pulse text-sm text-muted-foreground">
              Recherche dans les sources internes…
            </p>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-border p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSend(prompt)}
              className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="rounded-lg border border-border focus-within:border-primary/50">
          <Textarea
            ref={inputRef}
            rows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend(input)
              }
            }}
            placeholder="Décrivez le problème, collez une trace d'erreur ou demandez un runbook…"
            className="min-h-[5rem] resize-none border-0 bg-transparent focus-visible:ring-0"
          />
          <div className="flex items-center justify-between border-t border-border px-3 py-2">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <CornerDownLeft className="size-3" /> Entrée pour envoyer · Maj + Entrée pour un saut
              de ligne
            </p>
            <Button size="sm" disabled={!input.trim() || isStreaming} onClick={() => handleSend(input)}>
              <Send className="size-4" /> Envoyer
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export { ChatPanel }
