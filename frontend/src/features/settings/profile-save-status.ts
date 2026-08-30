/**
 * Where a profile save has got to.
 *
 * Five states rather than the old saved/failed pair, because a write to the identity
 * provider has one more outcome than either of those: accepted there, and not yet visible
 * here. Reporting that as success leaves the user looking at a header that still shows the
 * old name with no explanation; reporting it as failure is worse, since the change is real
 * and will arrive. It is its own outcome and says so.
 */
type ProfileSaveStatus =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "syncing" }
  | { kind: "saved" }
  | { kind: "pending" }
  | { kind: "error"; message: string }

interface ProfileSaveMessage {
  text: string
  tone: "muted" | "destructive"
}

function profileSaveMessage(status: ProfileSaveStatus): ProfileSaveMessage | null {
  switch (status.kind) {
    case "idle":
      return null
    case "saving":
      return { text: "Enregistrement…", tone: "muted" }
    case "syncing":
      return { text: "Synchronisation…", tone: "muted" }
    case "saved":
      return { text: "Modifications enregistrées", tone: "muted" }
    case "pending":
      return {
        text: "Enregistré. La synchronisation avec l'application est encore en cours ; l'affichage se mettra à jour automatiquement.",
        tone: "muted",
      }
    case "error":
      return { text: status.message, tone: "destructive" }
  }
}

export { profileSaveMessage }
export type { ProfileSaveStatus }
