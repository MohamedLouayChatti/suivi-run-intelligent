interface ChatSource {
  id: string
  label: string
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: ChatSource[]
}

interface ChatConversation {
  id: string
  title: string
  relativeTime: string
}

// Placeholder conversation seed for the Chatbot page. Replace with a real services/api/chatbot.ts
// call (backed by the conversational_assistant module, streamed via SSE) once it exists —
// consumers only depend on ChatMessage[], so swapping the source is a one-line change.
const initialMessages: ChatMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content:
      "Quelle est la mitigation standard pour le lag des consumers Kafka sur la passerelle de paiements ?",
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "La procédure documentée comporte trois étapes. D'abord, confirmez la source du lag dans le tableau de bord du groupe de consumers et vérifiez si le fournisseur en aval applique une limitation de débit. Ensuite, videz la file de reprise avant de scaler — scaler les consumers pendant que la file de reprise est saturée amplifie l'incident. Enfin, scalez le groupe de consumers d'une réplique à la fois et surveillez la latence de commit pendant cinq minutes entre chaque incrément.\n\nSi le lag reste au-dessus de 20 000 messages après deux incréments, escaladez vers l'astreinte plateforme plutôt que de continuer à scaler.",
    sources: [
      { id: "KB-118", label: "Runbook : vider la file de reprise en toute sécurité" },
      { id: "INC-2291", label: "Passerelle de paiements dégradée — timeouts fournisseur" },
      { id: "SR-4796", label: "Livraisons de webhooks dupliquées vers le sandbox partenaire" },
    ],
  },
]

const suggestedPrompts: string[] = [
  "Résumer les incidents Sev2 ouverts des 30 derniers jours",
  "Quel runbook couvre le renouvellement des certificats TLS ?",
  "Afficher les tickets similaires à SR-4821",
  "Expliquer la politique SLA pour les tickets de priorité critique",
]

// Placeholder conversation history for the right-hand panel. Replace with a real
// services/api/chatbot.ts call once it exists — consumers only depend on ChatConversation[].
const mockConversations: ChatConversation[] = [
  { id: "conv-1", title: "Procédure de lag des consumers Kafka", relativeTime: "il y a 18 min" },
  { id: "conv-2", title: "Rejouer la dead-letter queue", relativeTime: "il y a 2 h" },
  { id: "conv-3", title: "Politique SLA pour les incidents Sev2", relativeTime: "Hier" },
  { id: "conv-4", title: "Cache de jetons du service d'identité", relativeTime: "24 juil." },
  { id: "conv-5", title: "Dépassement de charge du Data Warehouse", relativeTime: "21 juil." },
]

function mockAssistantReply(): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content:
      "D'après les runbooks indexés et les tickets résolus des 90 derniers jours, la procédure documentée la plus proche est présentée ci-dessous. Deux incidents similaires ont été trouvés avec une signature comparable ; consultez-les avant d'appliquer un changement en production.",
    sources: [
      { id: "KB-204", label: "Procédure standard : changements en production" },
      { id: "INC-2288", label: "Panne partielle de l'Identity Service en EU-West" },
    ],
  }
}

export { initialMessages, suggestedPrompts, mockConversations, mockAssistantReply }
export type { ChatMessage, ChatSource, ChatConversation }
