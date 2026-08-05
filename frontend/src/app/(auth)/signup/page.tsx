"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useClerk, useSignUp } from "@clerk/nextjs";

import { AuthLayout } from "@/components/app/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  applicationOptions,
  functionalTeamLabels,
  functionalTeamOptions,
} from "@/features/tickets/constants";
import { PASSWORD_REQUIREMENTS_TEXT, isPasswordValid } from "@/features/auth/password";
import { clerkErrorMessage } from "@/features/auth/clerk-error";
import { VerificationCodeStep } from "@/features/auth/verification-code-step";

type Application = (typeof applicationOptions)[number];
type FunctionalTeam = (typeof functionalTeamOptions)[number];

export default function SignupPage() {
  const { signUp } = useSignUp();
  const { loaded: isClerkLoaded } = useClerk();
  const router = useRouter();

  const [step, setStep] = useState<"form" | "verify">("form");

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [application, setApplication] = useState<Application | "">("");
  const [functionalTeam, setFunctionalTeam] = useState<FunctionalTeam | "">("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function completeSignUp() {
    const { error: finalizeError } = await signUp.finalize();
    if (finalizeError) {
      setError(clerkErrorMessage(finalizeError));
      return;
    }
    router.push("/dashboard");
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting) return;

    if (!isPasswordValid(password)) {
      setError(PASSWORD_REQUIREMENTS_TEXT);
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: passwordError } = await signUp.password({
        emailAddress: email,
        password,
        firstName,
        lastName,
        unsafeMetadata: {
          application,
          functionalTeam,
        },
      });
      if (passwordError) {
        setError(clerkErrorMessage(passwordError));
        return;
      }

      if (signUp.status === "complete") {
        await completeSignUp();
        return;
      }

      const { error: sendError } = await signUp.verifications.sendEmailCode();
      if (sendError) {
        setError(clerkErrorMessage(sendError));
        return;
      }
      setStep("verify");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleVerify(event: FormEvent) {
    event.preventDefault();
    if (!isClerkLoaded || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const { error: verifyError } = await signUp.verifications.verifyEmailCode({ code });
      if (verifyError) {
        setError(clerkErrorMessage(verifyError));
        return;
      }

      if (signUp.status === "complete") {
        await completeSignUp();
        return;
      }

      setError("Vérification incomplète. Veuillez réessayer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResendCode() {
    if (!isClerkLoaded || isSubmitting) return;
    setError(null);
    const { error: sendError } = await signUp.verifications.sendEmailCode();
    if (sendError) setError(clerkErrorMessage(sendError));
  }

  if (step === "verify") {
    return (
      <AuthLayout
        title="Vérifiez votre e-mail"
        description={`Entrez le code envoyé à ${email}.`}
      >
        <VerificationCodeStep
          code={code}
          onCodeChange={setCode}
          onSubmit={handleVerify}
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
      title="Demande d'accès"
      description="Les comptes sont validés par un administrateur de la plateforme."
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="first">Prénom</Label>
            <Input
              id="first"
              required
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="last">Nom</Label>
            <Input
              id="last"
              required
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
          </div>
        </div>
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
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Application</Label>
            <Select
              value={application || undefined}
              onValueChange={(value) => setApplication(value as Application)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                {applicationOptions.map((app) => (
                  <SelectItem key={app} value={app}>
                    {app}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Équipe</Label>
            <Select
              value={functionalTeam || undefined}
              onValueChange={(value) => setFunctionalTeam(value as FunctionalTeam)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                {functionalTeamOptions.map((team) => (
                  <SelectItem key={team} value={team}>
                    {functionalTeamLabels[team]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Mot de passe</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <p className="text-xs text-muted-foreground">{PASSWORD_REQUIREMENTS_TEXT}</p>
        </div>

        <div id="clerk-captcha" />

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" className="w-full" disabled={!isClerkLoaded || isSubmitting}>
          {isSubmitting ? "Envoi en cours..." : "Soumettre la demande"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Vous avez déjà un compte ?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Se connecter
        </Link>
      </p>
    </AuthLayout>
  );
}
