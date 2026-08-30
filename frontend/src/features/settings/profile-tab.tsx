"use client"

import { useRef, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { functionalTeamLabels } from "@/features/users/constants"
import { useAuthSession } from "@/lib/auth/use-auth-session"
import { getPrimaryApplication, getBackupApplication, type CurrentUser } from "@/services/api/auth"

import { profileSaveMessage, type ProfileSaveStatus } from "./profile-save-status"
import { useProfileSync } from "./use-profile-sync"

const MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
const ACCEPTED_AVATAR_TYPES = ["image/png", "image/jpeg"]

interface ProfileTabProps {
  user: CurrentUser
  prenom: string
  nom: string
  onPrenomChange: (value: string) => void
  onNomChange: (value: string) => void
  status: ProfileSaveStatus
  onSave: () => void
}

function initials(prenom: string, nom: string): string {
  return `${prenom[0] ?? ""}${nom[0] ?? ""}`.toUpperCase()
}

function ProfileTab({ user, prenom, nom, onPrenomChange, onNomChange, status, onSave }: ProfileTabProps) {
  const primaryApplication = getPrimaryApplication(user)
  const backupApplication = getBackupApplication(user)
  const { imageUrl: clerkImageUrl, setProfileImage } = useAuthSession()
  const waitForSync = useProfileSync()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<ProfileSaveStatus>({ kind: "idle" })

  const saveMessage = profileSaveMessage(status)
  const uploadMessage = profileSaveMessage(uploadStatus)

  async function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return

    if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
      setUploadStatus({ kind: "error", message: "Le fichier doit être au format PNG ou JPG." })
      return
    }
    if (file.size > MAX_AVATAR_SIZE_BYTES) {
      setUploadStatus({ kind: "error", message: "Le fichier doit faire moins de 2 Mo." })
      return
    }

    // Captured before the upload, because "it changed" is the only thing that can be verified
    // here: the provider hosts the image and the URL it ends up published under is not the one
    // handed back by the upload call.
    const previousAvatarUrl = user.avatarUrl

    // No "Enregistrement…" here: the button already reads "Envoi en cours…" while this runs.
    setUploadStatus({ kind: "idle" })
    setIsUploading(true)
    try {
      await setProfileImage(file)
    } catch {
      setUploadStatus({ kind: "error", message: "Échec de l'envoi de la photo. Veuillez réessayer." })
      return
    } finally {
      setIsUploading(false)
    }

    // The avatar beside this button comes straight from the provider, so it is already the new
    // one. The header's does not — it renders what our own database holds — so the upload is
    // only finished once that has caught up, exactly as a name change is.
    setUploadStatus({ kind: "syncing" })
    const landed = await waitForSync((profile) => profile.avatarUrl !== previousAvatarUrl)
    setUploadStatus(landed ? { kind: "idle" } : { kind: "pending" })
  }

  return (
    <SectionCard
      title="Profil"
      description="Visible par les autres membres de l'équipe run"
      action={
        <div className="flex items-center gap-3">
          {saveMessage && (
            <span
              className={
                saveMessage.tone === "destructive"
                  ? "text-xs text-destructive"
                  : "text-xs text-muted-foreground"
              }
            >
              {saveMessage.text}
            </span>
          )}
          <Button size="sm" onClick={onSave} disabled={status.kind === "saving" || status.kind === "syncing"}>
            Enregistrer les modifications
          </Button>
        </div>
      }
    >
      <div className="flex items-center gap-4 border-b border-border pb-6">
        <Avatar size="lg">
          <AvatarImage src={clerkImageUrl ?? user.avatarUrl ?? undefined} alt={user.displayName} />
          <AvatarFallback>{initials(prenom, nom)}</AvatarFallback>
        </Avatar>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg"
            className="hidden"
            onChange={handleFileSelected}
          />
          <Button
            variant="outline"
            size="sm"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {isUploading ? "Envoi en cours…" : "Modifier la photo"}
          </Button>
          <p className="mt-2 text-xs text-muted-foreground">PNG ou JPG, jusqu&apos;à 2 Mo.</p>
          {uploadMessage && (
            <p
              className={
                uploadMessage.tone === "destructive"
                  ? "mt-1 text-xs text-destructive"
                  : "mt-1 text-xs text-muted-foreground"
              }
            >
              {uploadMessage.text}
            </p>
          )}
        </div>
      </div>
      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="prenom">Prénom</Label>
          <Input id="prenom" value={prenom} onChange={(e) => onPrenomChange(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="nom">Nom</Label>
          <Input id="nom" value={nom} onChange={(e) => onNomChange(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input id="email" type="email" defaultValue={user.email} readOnly className="bg-surface" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="team">Équipe</Label>
          <Input
            id="team"
            defaultValue={functionalTeamLabels[user.functionalTeam]}
            readOnly
            className="bg-surface"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="role">Rôle</Label>
          <Input id="role" defaultValue={user.role.name} readOnly className="bg-surface" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="primary-app">Application principale</Label>
          <Input id="primary-app" defaultValue={primaryApplication ?? "—"} readOnly className="bg-surface" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="backup-app">Application de secours</Label>
          <Input id="backup-app" defaultValue={backupApplication ?? "Aucune"} readOnly className="bg-surface" />
        </div>
      </div>
    </SectionCard>
  )
}

export { ProfileTab }
