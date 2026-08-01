import { SectionCard } from "@/components/app/page"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { functionalTeamLabels } from "@/features/users/constants"
import { getPrimaryApplication, getBackupApplication, type CurrentUser } from "@/services/api/auth"

interface ProfileTabProps {
  user: CurrentUser
  prenom: string
  nom: string
  onPrenomChange: (value: string) => void
  onNomChange: (value: string) => void
  justSaved: boolean
  onSave: () => void
}

function initials(prenom: string, nom: string): string {
  return `${prenom[0] ?? ""}${nom[0] ?? ""}`.toUpperCase()
}

function ProfileTab({ user, prenom, nom, onPrenomChange, onNomChange, justSaved, onSave }: ProfileTabProps) {
  const primaryApplication = getPrimaryApplication(user)
  const backupApplication = getBackupApplication(user)

  return (
    <SectionCard
      title="Profil"
      description="Visible par les autres membres de l'équipe run"
      action={
        <div className="flex items-center gap-3">
          {justSaved && (
            <span className="text-xs text-muted-foreground">Modifications enregistrées</span>
          )}
          <Button size="sm" onClick={onSave}>
            Enregistrer les modifications
          </Button>
        </div>
      }
    >
      <div className="flex items-center gap-4 border-b border-border pb-6">
        <Avatar size="lg">
          <AvatarFallback>{initials(prenom, nom)}</AvatarFallback>
        </Avatar>
        <div>
          <Button variant="outline" size="sm" disabled>
            Modifier la photo
          </Button>
          <p className="mt-2 text-xs text-muted-foreground">PNG ou JPG, jusqu&apos;à 2 Mo.</p>
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
          <Label htmlFor="email">Email</Label>
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
          <Input id="role" defaultValue={user.roles[0]?.name ?? "—"} readOnly className="bg-surface" />
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
