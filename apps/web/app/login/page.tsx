"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Check, KeyRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ProcureLogo } from "@/components/brand/logo";
import { API_URL } from "@/lib/utils";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(4),
});

type Form = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { email: "buyer@procure.ai", password: "demo12345" },
  });

  async function onSubmit(values: Form) {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    if (!res.ok) {
      form.setError("password", { message: "Invalid credentials" });
      toast.error("Sign in failed");
      return;
    }
    const data = (await res.json()) as { access_token: string };
    localStorage.setItem("procureai_token", data.access_token);
    router.push("/");
  }

  return (
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.2fr_.8fr]">
      <section className="relative flex min-h-[55vh] flex-col justify-between overflow-hidden bg-foreground p-8 text-background sm:p-12 lg:min-h-screen lg:p-16">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 18% 22%, #3d8e68 0%, transparent 42%), radial-gradient(circle at 88% 78%, #f7f6f3 0%, transparent 36%)",
          }}
        />
        <ProcureLogo inverse markClassName="h-9 w-9" />
        <div className="relative my-16 max-w-5xl">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-background/48">
            AI procurement intelligence
          </p>
          <h1 className="mt-7 text-5xl font-semibold leading-[0.94] tracking-[-0.055em] sm:text-6xl xl:text-[5.6rem]">
            Purchasing decisions,
            <br />
            <span className="text-background/40">executed & validated.</span>
          </h1>
          <p className="mt-8 max-w-xl text-[15px] leading-7 text-background/62">
            Investigate evidence, constrain recommendations, approve with intent, and verify every
            resulting purchase order against live operational state.
          </p>
        </div>
        <div className="relative grid gap-3 border-t border-background/12 pt-7 text-xs text-background/55 sm:grid-cols-3">
          {["Typed tool investigation", "Human approval controls", "Post-action recovery"].map(
            (item) => (
              <span key={item} className="flex items-center gap-2.5">
                <Check className="h-3.5 w-3.5 text-emerald-300" strokeWidth={2.2} />
                {item}
              </span>
            ),
          )}
        </div>
      </section>
      <section className="flex items-center justify-center bg-[hsl(var(--background))] p-8 sm:p-12">
        <div className="w-full max-w-md">
          <KeyRound className="h-5 w-5 text-primary" strokeWidth={1.75} />
          <p className="eyebrow mt-8">Secure operations console</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em]">Sign in to ProcureAI</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Use the seeded buyer account to run the golden demo path.
          </p>
          <form className="mt-8 space-y-5" onSubmit={form.handleSubmit(onSubmit)}>
            <label className="block text-xs font-medium">
              Work email
              <input className="input-base mt-2" autoComplete="email" {...form.register("email")} />
            </label>
            <label className="block text-xs font-medium">
              Password
              <input
                type="password"
                className="input-base mt-2"
                autoComplete="current-password"
                {...form.register("password")}
              />
            </label>
            {form.formState.errors.password && (
              <p className="text-xs text-destructive">{form.formState.errors.password.message}</p>
            )}
            <button className="button-primary w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Opening console…" : "Open procurement console"}{" "}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
          <div className="mt-8 border-t border-border pt-5 text-xs leading-5 text-muted-foreground">
            <p>
              <strong className="text-foreground">Buyer</strong> buyer@procure.ai · demo12345
            </p>
            <p>
              <strong className="text-foreground">Approver</strong> approver@procure.ai · demo12345
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
