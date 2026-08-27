import type { components } from "@/types/api"

import { httpClient } from "./client"

type CreateConversationResponse = components["schemas"]["CreateConversationResponse"]
type ConversationSummaryResponse = components["schemas"]["ConversationSummaryResponse"]
type PagedConversationSummary = components["schemas"]["PagedResponse_ConversationSummaryResponse_"]
type SendMessageResponse = components["schemas"]["SendMessageResponse"]
type ConversationMessagesResponse = components["schemas"]["ConversationMessagesResponse"]
type MessageResponse = components["schemas"]["MessageResponse"]
type RunSummaryResponse = components["schemas"]["RunSummaryResponse"]

async function createConversation(): Promise<CreateConversationResponse> {
  const { data } = await httpClient.post<CreateConversationResponse>(
    "/conversational-assistant/conversations",
  )
  return data
}

async function listConversations(page = 1, pageSize = 50): Promise<PagedConversationSummary> {
  const { data } = await httpClient.get<PagedConversationSummary>(
    "/conversational-assistant/conversations",
    { params: { page, page_size: pageSize } },
  )
  return data
}

async function sendMessage(conversationId: string, content: string): Promise<SendMessageResponse> {
  const { data } = await httpClient.post<SendMessageResponse>(
    `/conversational-assistant/conversations/${conversationId}/messages`,
    { content },
  )
  return data
}

async function getConversationMessages(
  conversationId: string,
  page = 1,
  pageSize = 50,
): Promise<ConversationMessagesResponse> {
  const { data } = await httpClient.get<ConversationMessagesResponse>(
    `/conversational-assistant/conversations/${conversationId}/messages`,
    { params: { page, page_size: pageSize } },
  )
  return data
}

export { createConversation, listConversations, sendMessage, getConversationMessages }
export type {
  CreateConversationResponse,
  ConversationSummaryResponse,
  PagedConversationSummary,
  SendMessageResponse,
  ConversationMessagesResponse,
  MessageResponse,
  RunSummaryResponse,
}
