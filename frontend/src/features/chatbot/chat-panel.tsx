"use client"

import { useEffect, useRef, useState } from "react"
import { Send, BookOpen, CornerDownLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ChatMessage } from "@/features/chatbot/chat-message"
import { suggestedPrompts, type ChatMessage as ChatMessageType } from "@/features/chatbot/types"

interface ChatPanelProps {
  messages: ChatMessageType[]
  isStreaming: boolean
  isLoadingMessages: boolean
  onSend: (content: string) => void
}

// How close to the bottom still counts as "following the answer". Wide enough that the last line
// of a growing message doesn't fall outside it between two deltas, narrow enough that a
// deliberate scroll up leaves it at once.
const STICK_TO_BOTTOM_THRESHOLD_PX = 80

function ChatPanel({ messages, isStreaming, isLoadingMessages, onSend }: ChatPanelProps) {
  const [input, setInput] = useState("")
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  // A ref, not state: it is read by the scroll effect and written by the scroll handler, and
  // nothing renders from it — as state, every wheel tick during a stream would re-render the
  // whole thread.
  const followingRef = useRef(true)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Scrolls the message list, never the document, and only while the reader is still at the
  // bottom. `scrollIntoView` on a sentinel used to do this: it re-fired on every streamed delta
  // and, because nothing above bounded the list's height, it moved the whole page — so scrolling
  // up during an answer was undone a few milliseconds later, repeatedly, until the stream ended.
  useEffect(() => {
    const list = listRef.current
    if (!list) return
    // An empty thread means a new or just-switched conversation: there is nothing the reader
    // could have scrolled away from, so following resumes.
    if (messages.length === 0) followingRef.current = true
    if (!followingRef.current) return
    list.scrollTop = list.scrollHeight
  }, [messages, isStreaming])

  function handleScroll() {
    const list = listRef.current
    if (!list) return
    followingRef.current =
      list.scrollHeight - list.scrollTop - list.clientHeight < STICK_TO_BOTTOM_THRESHOLD_PX
  }

  function handleSend(content: string) {
    if (!content.trim() || isStreaming) return
    // Sending is itself a request to watch the answer, whatever the reader had scrolled back to.
    followingRef.current = true
    onSend(content)
    setInput("")
    inputRef.current?.focus()
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-col rounded-lg border border-border bg-card">
      <div
        ref={listRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 space-y-8 overflow-y-auto p-6"
      >
        {isLoadingMessages && (
          <div className="py-10 text-center text-sm text-muted-foreground">Chargement de la conversation…</div>
        )}

        {!isLoadingMessages && messages.length === 0 && (
          <div className="mx-auto max-w-xl py-10 text-center">
            <div className="mx-auto grid size-11 place-items-center rounded-lg border border-border bg-surface">
              <BookOpen className="size-5 text-primary" strokeWidth={1.5} />
            </div>
            <h2 className="mt-4 text-sm font-semibold">Interrogez vos données opérationnelles</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Recherchez des tickets, explorez les incidents similaires et consultez vos indicateurs,
              tendances ou informations d&apos;équipe selon vos autorisations.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </div>

      <div className="shrink-0 border-t border-border p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSend(prompt)}
              disabled={isStreaming}
              className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
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
            placeholder="Recherchez un ticket, un incident similaire ou un indicateur d'activité…"
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
