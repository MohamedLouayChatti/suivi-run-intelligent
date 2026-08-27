"use client"

import { useEffect, useRef, useState } from "react"

import type { ChatMessage } from "@/features/chatbot/mock-data"
import { createConversation, sendMessage as sendMessageRequest } from "@/services/api/chatbot"
import { connectToAgentRunStream } from "@/services/sse/chatbot"

// Real chat loop for the Chatbot page, backed by the conversational_assistant module and
// streamed via SSE. Preserves the previous mock's public contract exactly:
// { messages, isStreaming, sendMessage, startNewConversation }.
//
// Starts with an empty conversation rather than reloading a previously selected one — there is
// no conversation picker wired up yet (ConversationsPanel is still on its own mock data), so
// there is nothing to reconcile against on mount. A conversation is created lazily, on the first
// message sent.
function useChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const conversationIdRef = useRef<string | null>(null)
  const closeStreamRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    return () => {
      closeStreamRef.current?.()
    }
  }, [])

  async function ensureConversation(): Promise<string> {
    if (conversationIdRef.current) return conversationIdRef.current
    const conversation = await createConversation()
    conversationIdRef.current = conversation.id
    return conversation.id
  }

  function updateAssistantMessage(assistantMessageId: string, content: string) {
    setMessages((prev) =>
      prev.map((message) => (message.id === assistantMessageId ? { ...message, content } : message)),
    )
  }

  function finishStreaming() {
    setIsStreaming(false)
    closeStreamRef.current?.()
    closeStreamRef.current = null
  }

  function openStream(runId: string, assistantMessageId: string) {
    closeStreamRef.current?.()
    let content = ""
    closeStreamRef.current = connectToAgentRunStream(runId, {
      onDelta: (event) => {
        content += event.content
        updateAssistantMessage(assistantMessageId, content)
      },
      onComplete: (message) => {
        updateAssistantMessage(assistantMessageId, message.content)
        finishStreaming()
      },
      onFailed: (event) => {
        updateAssistantMessage(assistantMessageId, event.failure_reason)
        finishStreaming()
      },
    })
  }

  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming) return

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content }])
    setIsStreaming(true)

    // The assistant bubble appears immediately, empty, and fills in live as message_delta
    // events arrive — there is no separate "thinking" placeholder outside `messages`.
    const assistantMessageId = crypto.randomUUID()
    setMessages((prev) => [...prev, { id: assistantMessageId, role: "assistant", content: "" }])

    try {
      const conversationId = await ensureConversation()
      const result = await sendMessageRequest(conversationId, content)
      openStream(result.run_id, assistantMessageId)
    } catch {
      updateAssistantMessage(assistantMessageId, "Une erreur est survenue. Veuillez réessayer.")
      setIsStreaming(false)
    }
  }

  function startNewConversation() {
    closeStreamRef.current?.()
    closeStreamRef.current = null
    conversationIdRef.current = null
    setMessages([])
    setIsStreaming(false)
  }

  return { messages, isStreaming, sendMessage, startNewConversation }
}

export { useChatbot }
