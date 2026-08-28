"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"

import { ChatbotHeader } from "@/features/chatbot/chatbot-header"
import { ChatPanel } from "@/features/chatbot/chat-panel"
import { CONVERSATION_QUERY_PARAM } from "@/features/chatbot/conversation-link"
import { ConversationsPanel } from "@/features/chatbot/conversations-panel"
import { useChatbot } from "@/features/chatbot/use-chatbot"

export default function ChatbotPage() {
  return (
    <Suspense fallback={null}>
      <ChatbotPageContent />
    </Suspense>
  )
}

function ChatbotPageContent() {
  // Only ever an opening selection — see conversation-link.ts. Picking another conversation from
  // the panel does not rewrite the URL, so this is read once and never again.
  const initialConversationId = useSearchParams().get(CONVERSATION_QUERY_PARAM)
  const {
    messages,
    isStreaming,
    isLoadingMessages,
    sendMessage,
    startNewConversation,
    conversations,
    isLoadingConversations,
    activeConversationId,
    selectConversation,
  } = useChatbot(initialConversationId)

  return (
    // The one page in the app that is a fixed-height workspace rather than a document: the chat
    // pane and the conversation list each scroll inside themselves, so a streaming answer never
    // moves the page under the reader and the composer never scrolls out of reach. Hence the
    // explicit height instead of PageBody's `flex-1` — 3.5rem is SiteHeader's own `h-14`, the
    // only chrome above this. `min-h` keeps it usable on a short viewport by letting the
    // document scroll again rather than crushing the thread.
    <div className="flex h-[calc(100svh-3.5rem)] min-h-[40rem] flex-col">
      <ChatbotHeader onNewConversation={startNewConversation} />
      <div className="mx-auto grid min-h-0 w-full max-w-[112rem] flex-1 gap-6 px-4 py-6 md:px-8 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <ChatPanel
          messages={messages}
          isStreaming={isStreaming}
          isLoadingMessages={isLoadingMessages}
          onSend={sendMessage}
        />
        <ConversationsPanel
          conversations={conversations}
          activeConversationId={activeConversationId}
          isLoading={isLoadingConversations}
          onSelect={selectConversation}
        />
      </div>
    </div>
  )
}
