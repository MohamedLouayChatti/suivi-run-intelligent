"use client"

import { useState } from "react"

import { initialMessages, mockAssistantReply, type ChatMessage } from "@/features/chatbot/mock-data"

const REPLY_DELAY_MS = 1400

// Placeholder chat loop for the Chatbot page. Replace with a real services/api/chatbot.ts call
// (SSE stream from the conversational_assistant module) once it exists — consumers only depend
// on { messages, isStreaming, sendMessage, startNewConversation }, so swapping the implementation
// is a one-line change.
function useChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [isStreaming, setIsStreaming] = useState(false)

  function sendMessage(content: string) {
    if (!content.trim() || isStreaming) return

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content }])
    setIsStreaming(true)

    setTimeout(() => {
      setMessages((prev) => [...prev, mockAssistantReply()])
      setIsStreaming(false)
    }, REPLY_DELAY_MS)
  }

  function startNewConversation() {
    setMessages([])
  }

  return { messages, isStreaming, sendMessage, startNewConversation }
}

export { useChatbot }
