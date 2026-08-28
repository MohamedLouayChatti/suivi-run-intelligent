/**
 * How another page points at one conversation. The Chatbot page otherwise keeps the active
 * conversation in local state — this parameter is only ever an *initial* selection, read once on
 * mount, so picking a different conversation there does not rewrite the URL.
 *
 * One file rather than a string built at each call site, so the page reading the parameter and the
 * links writing it cannot disagree about its name.
 */
const CONVERSATION_QUERY_PARAM = "conversation"

function conversationHref(conversationId: string): string {
  return `/chatbot?${CONVERSATION_QUERY_PARAM}=${conversationId}`
}

export { CONVERSATION_QUERY_PARAM, conversationHref }
