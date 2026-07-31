"use client"

import { useState } from "react"

import { PageHeader, PageBody } from "@/components/app/page"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { useCurrentUser } from "@/hooks/use-current-user"
import { ProfileTab } from "@/features/settings/profile-tab"
import { AppearanceTab } from "@/features/settings/appearance-tab"

function splitDisplayName(displayName: string): { prenom: string; nom: string } {
  const [prenom = "", ...rest] = displayName.split(" ")
  return { prenom, nom: rest.join(" ") }
}

export default function SettingsPage() {
  const user = useCurrentUser()
  const [{ prenom, nom }, setName] = useState(() => splitDisplayName(user.display_name))
  const [justSaved, setJustSaved] = useState(false)

  function handleSave() {
    setJustSaved(true)
    setTimeout(() => setJustSaved(false), 2000)
  }

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
          </TabsList>

          <TabsContent value="profile">
            <ProfileTab
              user={user}
              prenom={prenom}
              nom={nom}
              onPrenomChange={(value) => setName((n) => ({ ...n, prenom: value }))}
              onNomChange={(value) => setName((n) => ({ ...n, nom: value }))}
              justSaved={justSaved}
              onSave={handleSave}
            />
          </TabsContent>

          <TabsContent value="appearance">
            <AppearanceTab />
          </TabsContent>
        </Tabs>
      </PageBody>
    </>
  )
}
