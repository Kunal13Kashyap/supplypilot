"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { getToken } from "@/lib/utils";
import { AppShell } from "@/components/app-shell";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);
  if (typeof window !== "undefined" && !getToken()) return null;
  return <AppShell>{children}</AppShell>;
}
