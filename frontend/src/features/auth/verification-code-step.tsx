"use client";

import type { FormEvent, ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface VerificationCodeStepProps {
  code: string;
  onCodeChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  isSubmitting: boolean;
  submitLabel: string;
  submittingLabel: string;
  error?: string | null;
  /** Extra fields rendered between the code input and the submit button (e.g. a new password field). */
  children?: ReactNode;
  /** Rendered below the form, e.g. a "resend code" or "back" link. */
  footer?: ReactNode;
}

/**
 * The "enter the one-time code" step shared by every Clerk custom flow that pauses on a
 * code verification (sign-up email verification, password-reset code, Client Trust
 * second-factor verification on login) — kept in one place instead of duplicated per page.
 */
function VerificationCodeStep({
  code,
  onCodeChange,
  onSubmit,
  isSubmitting,
  submitLabel,
  submittingLabel,
  error,
  children,
  footer,
}: VerificationCodeStepProps) {
  return (
    <>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <Label htmlFor="code">Code de vérification</Label>
          <Input
            id="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={code}
            onChange={(event) => onCodeChange(event.target.value)}
          />
        </div>

        {children}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? submittingLabel : submitLabel}
        </Button>
      </form>
      {footer}
    </>
  );
}

export { VerificationCodeStep };
