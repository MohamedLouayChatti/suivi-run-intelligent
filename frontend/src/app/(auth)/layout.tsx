import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

/**
 * Resource-based guard (mirrors app/(protected)/layout.tsx): an already-signed-in Clerk
 * session should never see login/signup/forgot-password again — reaching this page while
 * signed in as someone else is exactly how a second identity gets layered on top of the
 * first without an explicit logout. Force a redirect instead of letting the form submit.
 */
export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();
  if (userId) {
    redirect("/dashboard");
  }

  return <div className="flex flex-1 flex-col">{children}</div>;
}
