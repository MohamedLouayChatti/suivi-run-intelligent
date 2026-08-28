"use client"

import { useEffect, useRef, useState } from "react"
import { ArrowDown, Send, BookOpen, CornerDownLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ChatMessage } from "@/features/chatbot/chat-message"
import { type ChatMessage as ChatMessageType } from "@/features/chatbot/types"

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
  // Unlike followingRef, this does need to be state — it drives whether the scroll-to-bottom
  // button renders at all.
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)

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
    // could have scrolled away from, so following resumes. The scroll-to-bottom button's own
    // visibility is guarded by `messages.length > 0` below rather than reset here — setting
    // state synchronously inside an effect risks cascading renders.
    if (messages.length === 0) followingRef.current = true
    if (!followingRef.current) return
    list.scrollTop = list.scrollHeight
  }, [messages, isStreaming])

  function handleScroll() {
    const list = listRef.current
    if (!list) return
    const atBottom =
      list.scrollHeight - list.scrollTop - list.clientHeight < STICK_TO_BOTTOM_THRESHOLD_PX
    followingRef.current = atBottom
    setShowScrollToBottom(!atBottom)
  }

  function scrollToBottom() {
    const list = listRef.current
    if (!list) return
    followingRef.current = true
    setShowScrollToBottom(false)
    list.scrollTo({ top: list.scrollHeight, behavior: "smooth" })
  }

  function handleSend(content: string) {
    if (!content.trim() || isStreaming) return
    // Sending is itself a request to watch the answer, whatever the reader had scrolled back to.
    followingRef.current = true
    setShowScrollToBottom(false)
    onSend(content)
    setInput("")
    inputRef.current?.focus()
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-col rounded-lg border border-border bg-card">
      <div className="relative min-h-0 flex-1">
        <div ref={listRef} onScroll={handleScroll} className="h-full space-y-8 overflow-y-auto p-6">
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

          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              message={message}
              isPending={
                isStreaming &&
                index === messages.length - 1 &&
                message.role === "ASSISTANT" &&
                !message.failed &&
                message.content.length === 0
              }
            />
          ))}
        </div>

        {showScrollToBottom && messages.length > 0 && (
          <button
            type="button"
            onClick={scrollToBottom}
            aria-label="Aller en bas de la conversation"
            className="absolute bottom-4 left-1/2 grid size-9 -translate-x-1/2 place-items-center rounded-full border border-border bg-background text-foreground shadow-md transition-colors hover:bg-surface"
          >
            <ArrowDown className="size-4" />
          </button>
        )}
      </div>

      <div className="shrink-0 border-t border-border p-4">
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
