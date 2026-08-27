import { Plus } from "lucide-react"

import { PageHeader } from "@/components/app/page"
import { Button } from "@/components/ui/button"

interface ChatbotHeaderProps {
  onNewConversation: () => void
}

function ChatbotHeader({ onNewConversation }: ChatbotHeaderProps) {
  return (
    <PageHeader
      title="Assistant IA"
      description="Recherchez et analysez les données de tickets auxquelles vous avez accès."
      actions={
        <Button variant="outline" size="sm" onClick={onNewConversation}>
          <Plus className="size-4" /> Nouvelle conversation
        </Button>
      }
    />
  )
}

export { ChatbotHeader }
