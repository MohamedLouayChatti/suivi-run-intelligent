"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type PasswordInputProps = Omit<React.ComponentProps<typeof Input>, "type">;

function PasswordInput({ className, ...props }: PasswordInputProps) {
  const [isVisible, setIsVisible] = useState(false);

  function hidePassword() {
    setIsVisible(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setIsVisible(true);
    }
  }

  function handleKeyUp(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      hidePassword();
    }
  }

  return (
    <div className="relative">
      <Input
        {...props}
        type={isVisible ? "text" : "password"}
        className={cn("pr-10", className)}
      />
      <button
        type="button"
        aria-label={isVisible ? "Masquer le mot de passe" : "Maintenir pour afficher le mot de passe"}
        className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onPointerDown={(event) => {
          event.preventDefault();
          setIsVisible(true);
        }}
        onPointerUp={hidePassword}
        onPointerCancel={hidePassword}
        onPointerLeave={hidePassword}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        onBlur={hidePassword}
        onContextMenu={(event) => event.preventDefault()}
      >
        {isVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
      </button>
    </div>
  );
}

export { PasswordInput };
