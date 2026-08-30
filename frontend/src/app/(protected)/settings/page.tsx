"use client"

import { useState } from "react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { useCurrentUser } from "@/lib/auth"
import { useAuthSession } from "@/lib/auth/use-auth-session"
import { ProfileTab } from "@/features/settings/profile-tab"
import { AppearanceTab } from "@/features/settings/appearance-tab"
import { SecurityTab } from "@/features/settings/security-tab"
import { useProfileSync } from "@/features/settings/use-profile-sync"
import type { ProfileSaveStatus } from "@/features/settings/profile-save-status"

/** How long "Modifications enregistrées" stays up before the form goes quiet again. */
const SAVED_NOTICE_MS = 2000

export default function SettingsPage() {
  const { data: user } = useCurrentUser()
  const { setProfileName } = useAuthSession()
  const waitForSync = useProfileSync()

  // The two halves as the backend holds them — no splitting here any more. The form used to
  // cut `display_name` at its first space, which is not the inverse of the join that produced
  // it: a given name of two words came back as a surname, and saving wrote that back.
  const serverPrenom = user?.firstName ?? ""
  const serverNom = user?.lastName ?? ""

  const [{ prenom, nom }, setName] = useState({ prenom: serverPrenom, nom: serverNom })
  const [seededFrom, setSeededFrom] = useState({ prenom: serverPrenom, nom: serverNom })
  const [status, setStatus] = useState<ProfileSaveStatus>({ kind: "idle" })

  // Re-seeded whenever the server's own values change, rather than read once at mount. That
  // is what lets a save be *verified*: the sync poll refetches until the profile reports what
  // was submitted, and this reconciles the form with it. When the change never arrives the
  // server values never change, so the fields keep what was typed instead of silently
  // reverting to a name the identity provider no longer holds.
  //
  // Adjusted during render rather than in an effect — React's own advice for resetting state
  // when the value it was derived from changes, and the shape the lint rule here insists on.
  // The re-render happens before anything is committed, so no intermediate state is painted.
  if (seededFrom.prenom !== serverPrenom || seededFrom.nom !== serverNom) {
    setSeededFrom({ prenom: serverPrenom, nom: serverNom })
    setName({ prenom: serverPrenom, nom: serverNom })
  }

  async function handleSave() {
    const trimmedPrenom = prenom.trim()
    const trimmedNom = nom.trim()
    if (!trimmedPrenom && !trimmedNom) {
      setStatus({ kind: "error", message: "Le nom et le prénom sont obligatoires." })
      return
    }
    if (!trimmedNom) {
      setStatus({ kind: "error", message: "Le nom est obligatoire." })
      return
    }
    if (!trimmedPrenom) {
      setStatus({ kind: "error", message: "Le prénom est obligatoire." })
      return
    }

    setStatus({ kind: "saving" })
    try {
      await setProfileName(trimmedPrenom, trimmedNom)
    } catch {
      // Nothing was written anywhere, so the form goes back to what the account actually
      // holds rather than leaving a rejected edit on screen looking saved.
      setName({ prenom: serverPrenom, nom: serverNom })
      setStatus({
        kind: "error",
        message: "Impossible d'enregistrer les modifications. Veuillez réessayer.",
      })
      return
    }

    setStatus({ kind: "syncing" })
    const landed = await waitForSync(
      (profile) => profile.firstName === trimmedPrenom && profile.lastName === trimmedNom,
    )
    if (!landed) {
      setStatus({ kind: "pending" })
      return
    }
    setStatus({ kind: "saved" })
    setTimeout(() => setStatus({ kind: "idle" }), SAVED_NOTICE_MS)
  }

  if (!user) return null

  return (
    <>
      <PageHeader
        title="Paramètres"
        description="Paramètres personnels de votre compte"
        breadcrumbs={[{ label: "Suivi Run", href: "/" }, { label: "Paramètres" }]}
      />
      <PageBody>
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile">Profil</TabsTrigger>
            <TabsTrigger value="appearance">Apparence</TabsTrigger>
            <TabsTrigger value="security">Sécurité</TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <ProfileTab
              user={user}
              prenom={prenom}
              nom={nom}
              onPrenomChange={(value) => setName((n) => ({ ...n, prenom: value }))}
              onNomChange={(value) => setName((n) => ({ ...n, nom: value }))}
              status={status}
              onSave={handleSave}
            />
          </TabsContent>

          <TabsContent value="appearance">
            <AppearanceTab />
          </TabsContent>

          <TabsContent value="security">
            <SecurityTab />
          </TabsContent>
        </Tabs>
      </PageBody>
    </>
  )
}
