"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useClerk, useSignIn } from "@clerk/nextjs";

import { AuthLayout } from "@/components/app/auth-layout";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { PASSWORD_REQUIREMENTS_TEXT, isPasswordValid } from "@/features/auth/password";
import { clerkErrorMessage } from "@/features/auth/clerk-error";
import { VerificationCodeStep } from "@/features/auth/verification-code-step";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  const { signIn } = useSignIn();
  const { loaded: isClerkLoaded } = useClerk();
  const router = useRouter();

  const [step, setStep] = useState<"request" | "reset">("request");

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleRequestCode(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: createError } = await signIn.create({ identifier: email });
      if (createError) {
        setError(clerkErrorMessage(createError));
        return;
      }

      const { error: sendError } = await signIn.resetPasswordEmailCode.sendCode();
      if (sendError) {
        setError(clerkErrorMessage(sendError));
        return;
      }
      setStep("reset");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResetPassword(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting) return;

    if (password !== passwordConfirmation) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    if (!isPasswordValid(password)) {
      setError(PASSWORD_REQUIREMENTS_TEXT);
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: verifyError } = await signIn.resetPasswordEmailCode.verifyCode({ code });
      if (verifyError) {
        setError(clerkErrorMessage(verifyError));
        return;
      }

      const { error: submitError } = await signIn.resetPasswordEmailCode.submitPassword({
        password,
      });
      if (submitError) {
        setError(clerkErrorMessage(submitError));
        return;
      }

      if (signIn.status === "complete") {
        const { error: finalizeError } = await signIn.finalize();
        if (finalizeError) {
          setError(clerkErrorMessage(finalizeError));
          return;
        }
        router.push("/dashboard");
        return;
      }

      setError("Réinitialisation incomplète. Veuillez réessayer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (step === "reset") {
    return (
      <AuthLayout
        title="Réinitialiser le mot de passe"
        description={`Entrez le code envoyé à ${email} et choisissez un nouveau mot de passe.`}
      >
        <VerificationCodeStep
          code={code}
          onCodeChange={setCode}
          onSubmit={handleResetPassword}
          isSubmitting={isSubmitting}
          submitLabel="Réinitialiser le mot de passe"
          submittingLabel="Réinitialisation..."
          error={error}
        >
          <div className="space-y-2">
            <Label htmlFor="password">Nouveau mot de passe</Label>
            <PasswordInput
              id="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <p className="text-xs text-muted-foreground">{PASSWORD_REQUIREMENTS_TEXT}</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password-confirmation">Confirmer le mot de passe</Label>
            <PasswordInput
              id="password-confirmation"
              autoComplete="new-password"
              required
              value={passwordConfirmation}
              onChange={(event) => setPasswordConfirmation(event.target.value)}
            />
          </div>
        </VerificationCodeStep>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Mot de passe oublié"
      description="Indiquez votre e-mail professionnel pour recevoir un code de réinitialisation."
    >
      <form className="space-y-4" onSubmit={handleRequestCode}>
        <div className="space-y-2">
          <Label htmlFor="email">E-mail professionnel</Label>
          <Input
            id="email"
            type="email"
            placeholder="nom@sofrecom.com"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" className="w-full" disabled={!isClerkLoaded || isSubmitting}>
          {isSubmitting ? "Envoi en cours..." : "Envoyer le code"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-primary hover:underline">
          Retour à la connexion
        </Link>
      </p>
    </AuthLayout>
  );
}
