"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useClerk, useSignIn } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";

import { AuthLayout } from "@/components/app/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { clerkErrorMessage } from "@/features/auth/clerk-error";
import { VerificationCodeStep } from "@/features/auth/verification-code-step";

type SecondFactorStrategy = "email_code" | "phone_code";

interface SecondFactor {
  strategy: SecondFactorStrategy;
  safeIdentifier: string;
}

/**
 * Picks the second factor Client Trust should use to verify this device: prefers
 * `email_code` (matches the verification UX already used elsewhere in this flow),
 * falls back to `phone_code` if that's the only one the Clerk Dashboard config supports.
 */
function pickSecondFactor(
  factors: ReadonlyArray<{ strategy: string; safeIdentifier?: string }>,
): SecondFactor | null {
  for (const strategy of ["email_code", "phone_code"] as const) {
    const factor = factors.find((candidate) => candidate.strategy === strategy);
    if (factor?.safeIdentifier) return { strategy, safeIdentifier: factor.safeIdentifier };
  }
  return null;
}

export default function LoginPage() {
  const { signIn } = useSignIn();
  const { loaded: isClerkLoaded } = useClerk();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSignedIn, setKeepSignedIn] = useState(false);
  const [code, setCode] = useState("");
  const [secondFactor, setSecondFactor] = useState<SecondFactor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function sendSecondFactorCode(strategy: SecondFactorStrategy) {
    return strategy === "email_code" ? signIn.mfa.sendEmailCode() : signIn.mfa.sendPhoneCode();
  }

  async function completeSignIn() {
    const { error: finalizeError } = await signIn.finalize();
    if (finalizeError) {
      setError(clerkErrorMessage(finalizeError));
      return;
    }
    // Wipe any state cached under the previous session (e.g. another user who never
    // clicked "Se déconnecter") so the dashboard never renders stale identity/data.
    queryClient.clear();
    router.push("/dashboard");
  }

  async function handleCredentialsSubmit(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: passwordError } = await signIn.password({ identifier: email, password });
      if (passwordError) {
        setError(clerkErrorMessage(passwordError));
        return;
      }

      switch (signIn.status) {
        case "complete":
          await completeSignIn();
          return;
        case "needs_client_trust": {
          const factor = pickSecondFactor(signIn.supportedSecondFactors);
          if (!factor) {
            setError(
              "Vérification supplémentaire requise mais non prise en charge. Contactez un administrateur.",
            );
            return;
          }
          const { error: sendError } = await sendSecondFactorCode(factor.strategy);
          if (sendError) {
            setError(clerkErrorMessage(sendError));
            return;
          }
          setSecondFactor(factor);
          return;
        }
        default:
          setError("Connexion incomplète. Veuillez réessayer.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleVerifySubmit(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting || !secondFactor) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: verifyError } =
        secondFactor.strategy === "email_code"
          ? await signIn.mfa.verifyEmailCode({ code })
          : await signIn.mfa.verifyPhoneCode({ code });
      if (verifyError) {
        setError(clerkErrorMessage(verifyError));
        return;
      }

      if (signIn.status === "complete") {
        await completeSignIn();
        return;
      }

      setError("Vérification incomplète. Veuillez réessayer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResendCode() {
    if (!isClerkLoaded || isSubmitting || !secondFactor) return;
    setError(null);
    const { error: sendError } = await sendSecondFactorCode(secondFactor.strategy);
    if (sendError) setError(clerkErrorMessage(sendError));
  }

  if (secondFactor) {
    return (
      <AuthLayout
        title="Vérification supplémentaire"
        description={`Nouvel appareil détecté. Entrez le code envoyé à ${secondFactor.safeIdentifier}.`}
      >
        <VerificationCodeStep
          code={code}
          onCodeChange={setCode}
          onSubmit={handleVerifySubmit}
          isSubmitting={isSubmitting}
          submitLabel="Vérifier"
          submittingLabel="Vérification..."
          error={error}
          footer={
            <p className="mt-6 text-center text-sm text-muted-foreground">
              Vous n&apos;avez rien reçu ?{" "}
              <button
                type="button"
                onClick={handleResendCode}
                className="font-medium text-primary hover:underline"
              >
                Renvoyer le code
              </button>
            </p>
          }
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Connexion"
      description="Utilisez votre compte professionnel pour accéder à la console."
    >
      <form className="space-y-4" onSubmit={handleCredentialsSubmit}>
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
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Mot de passe</Label>
            <Link
              href="/forgot-password"
              className="text-xs text-primary hover:underline"
            >
              Mot de passe oublié ?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" className="w-full" disabled={!isClerkLoaded || isSubmitting}>
          {isSubmitting ? "Connexion en cours..." : "Se connecter"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Pas encore de compte ?{" "}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          Demander l&apos;accès
        </Link>
      </p>
    </AuthLayout>
  );
}
