"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignUp } from "@clerk/nextjs/legacy";

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
import { getClerkErrorMessage } from "@/features/auth/clerk-error";

type Application = (typeof applicationOptions)[number];
type FunctionalTeam = (typeof functionalTeamOptions)[number];

export default function SignupPage() {
  const { isLoaded, signUp, setActive } = useSignUp();
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

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!isLoaded || isSubmitting) return;

    if (!isPasswordValid(password)) {
      setError(PASSWORD_REQUIREMENTS_TEXT);
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await signUp.create({
        emailAddress: email,
        password,
        firstName,
        lastName,
        unsafeMetadata: {
          application,
          functionalTeam,
        },
      });

      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
      setStep("verify");
    } catch (err) {
      setError(getClerkErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleVerify(event: FormEvent) {
    event.preventDefault();
    if (!isLoaded || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    try {
      const result = await signUp.attemptEmailAddressVerification({ code });

      if (result.status === "complete") {
        await setActive({ session: result.createdSessionId });
        router.push("/dashboard");
        return;
      }

      setError("Vérification incomplète. Veuillez réessayer.");
    } catch (err) {
      setError(getClerkErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResendCode() {
    if (!isLoaded || isSubmitting) return;
    setError(null);
    try {
      await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
    } catch (err) {
      setError(getClerkErrorMessage(err));
    }
  }

  if (step === "verify") {
    return (
      <AuthLayout
        title="Vérifiez votre e-mail"
        description={`Entrez le code envoyé à ${email}.`}
      >
        <form className="space-y-4" onSubmit={handleVerify}>
          <div className="space-y-2">
            <Label htmlFor="code">Code de vérification</Label>
            <Input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              required
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" className="w-full" disabled={!isLoaded || isSubmitting}>
            {isSubmitting ? "Vérification..." : "Vérifier"}
          </Button>
        </form>
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
            placeholder="nom@interne.io"
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

        <Button type="submit" className="w-full" disabled={!isLoaded || isSubmitting}>
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
