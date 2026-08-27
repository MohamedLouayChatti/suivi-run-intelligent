"use client"

import { type FormEvent, useState } from "react"
import { useReverification, useSession } from "@clerk/nextjs"
import { isReverificationCancelledError } from "@clerk/nextjs/errors"

import { SectionCard } from "@/components/app/page"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { PasswordInput } from "@/components/ui/password-input"
import { PASSWORD_REQUIREMENTS_TEXT, isPasswordValid } from "@/features/auth/password"
import { clerkThrownErrorMessage } from "@/features/auth/clerk-error"
import { useAuthSession } from "@/lib/auth/use-auth-session"

function SecurityTab() {
  const { updatePassword } = useAuthSession()
  const { session } = useSession()

  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [newPasswordConfirmation, setNewPasswordConfirmation] = useState("")
  const [signOutOfOtherSessions, setSignOutOfOtherSessions] = useState(true)

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [justSaved, setJustSaved] = useState(false)

  // Updating a password is a Clerk-sensitive action that can demand session
  // reverification. Rather than showing Clerk's own (unstyled, English-first) modal and
  // asking for the current password a second time, `onNeedsReverification` satisfies it
  // ourselves with the password already entered above, so the retry that follows
  // `complete()` succeeds silently and no popup ever appears.
  const updatePasswordWithReverification = useReverification(
    async () => {
      await updatePassword({ currentPassword, newPassword, signOutOfOtherSessions })
    },
    {
      onNeedsReverification: async ({ cancel, complete, level }) => {
        if (!session) {
          setError("Une erreur est survenue. Veuillez réessayer.")
          cancel()
          return
        }
        try {
          await session.startVerification({ level: level ?? "first_factor" })
          const attempt = await session.attemptFirstFactorVerification({
            strategy: "password",
            password: currentPassword,
          })
          if (attempt.status === "complete") {
            complete()
          } else {
            setError("Mot de passe actuel incorrect.")
            cancel()
          }
        } catch (err) {
          setError(clerkThrownErrorMessage(err))
          cancel()
        }
      },
    },
  )

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (isSubmitting) return

    setError(null)
    setJustSaved(false)

    if (newPassword !== newPasswordConfirmation) {
      setError("Les mots de passe ne correspondent pas.")
      return
    }
    if (!isPasswordValid(newPassword)) {
      setError(PASSWORD_REQUIREMENTS_TEXT)
      return
    }

    setIsSubmitting(true)
    try {
      await updatePasswordWithReverification()
      setCurrentPassword("")
      setNewPassword("")
      setNewPasswordConfirmation("")
      setJustSaved(true)
      setTimeout(() => setJustSaved(false), 2000)
    } catch (err) {
      // A cancelled reverification means `onNeedsReverification` already set the specific
      // reason (wrong password, etc.) — don't overwrite it with this generic runtime error.
      if (!isReverificationCancelledError(err)) {
        setError(clerkThrownErrorMessage(err))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <SectionCard title="Sécurité" description="Mot de passe utilisé pour vous connecter">
      <form className="max-w-sm space-y-5" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <Label htmlFor="current-password">Mot de passe actuel</Label>
          <PasswordInput
            id="current-password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="new-password">Nouveau mot de passe</Label>
          <PasswordInput
            id="new-password"
            autoComplete="new-password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">{PASSWORD_REQUIREMENTS_TEXT}</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="new-password-confirmation">Confirmer le nouveau mot de passe</Label>
          <PasswordInput
            id="new-password-confirmation"
            autoComplete="new-password"
            required
            value={newPasswordConfirmation}
            onChange={(e) => setNewPasswordConfirmation(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            id="sign-out-other-sessions"
            checked={signOutOfOtherSessions}
            onCheckedChange={(checked) => setSignOutOfOtherSessions(checked === true)}
          />
          <Label htmlFor="sign-out-other-sessions" className="font-normal text-muted-foreground">
            Se déconnecter des autres appareils
          </Label>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" size="sm" disabled={isSubmitting}>
            {isSubmitting ? "Mise à jour..." : "Mettre à jour le mot de passe"}
          </Button>
          {justSaved && (
            <span className="text-xs text-muted-foreground">Mot de passe mis à jour</span>
          )}
          {error && <span className="text-xs text-destructive">{error}</span>}
        </div>
      </form>
    </SectionCard>
  )
}

export { SecurityTab }
