"use client"

import { PageBody } from "@/components/app/page"
import { ChatbotHeader } from "@/features/chatbot/chatbot-header"
import { ChatPanel } from "@/features/chatbot/chat-panel"
import { ConversationsPanel } from "@/features/chatbot/conversations-panel"
import { useChatbot } from "@/features/chatbot/use-chatbot"

export default function ChatbotPage() {
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
  } = useChatbot()

  return (
    <>
      <ChatbotHeader onNewConversation={startNewConversation} />
      <PageBody className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_18rem]">
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
      </PageBody>
    </>
  )
}
