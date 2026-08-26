"use client"

import { useState } from "react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { useCurrentUser } from "@/lib/auth"
import { useAuthSession } from "@/lib/auth/use-auth-session"
import { ProfileTab } from "@/features/settings/profile-tab"
import { AppearanceTab } from "@/features/settings/appearance-tab"
import { SecurityTab } from "@/features/settings/security-tab"

function splitDisplayName(displayName: string): { prenom: string; nom: string } {
  const [prenom = "", ...rest] = displayName.split(" ")
  return { prenom, nom: rest.join(" ") }
}

export default function SettingsPage() {
  const { data: user } = useCurrentUser()
  const { setProfileName } = useAuthSession()
  const [{ prenom, nom }, setName] = useState(() => splitDisplayName(user?.displayName ?? ""))
  const [justSaved, setJustSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  async function handleSave() {
    setJustSaved(false)
    setSaveError(null)

    const trimmedPrenom = prenom.trim()
    const trimmedNom = nom.trim()
    if (!trimmedNom) {
      if(!trimmedPrenom) {
        setSaveError("Le nom et le prénom sont obligatoires.")
        return
      }
      setSaveError("Le nom est obligatoire.")
      return
    }
    if (!trimmedPrenom) {
      setSaveError("Le prénom est obligatoire.")
      return
    }

    try {
      await setProfileName(trimmedPrenom, trimmedNom)
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000)
    } catch {
      setSaveError("Impossible d'enregistrer les modifications. Veuillez réessayer.")
    }
  }

  if (!user) return null

  return (
    <>
      <PageHeader
        title="Paramètres"
        description="Configuration personnelle de votre compte"
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
              justSaved={justSaved}
              saveError={saveError}
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
