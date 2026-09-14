"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  Bell,
  BookOpen,
  Boxes,
  ChevronRight,
  ClipboardList,
  Command,
  LayoutDashboard,
  Menu,
  Moon,
  Search,
  ScrollText,
  ShoppingCart,
  Sun,
  Truck,
  X,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { ProcureLogo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/cases", label: "Purchasing Cases", icon: ClipboardList },
  { href: "/purchase-orders", label: "Purchase Orders", icon: ShoppingCart },
  { href: "/suppliers", label: "Suppliers", icon: Truck },
  { href: "/inventory", label: "Inventory", icon: Boxes },
  { href: "/agent-runs", label: "Agent Runs", icon: Activity },
  { href: "/audit", label: "Audit Logs", icon: ScrollText },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { resolvedTheme, setTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const segments = pathname.split("/").filter(Boolean);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((value) => !value);
      }
      if (event.key === "Escape") setCommandOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const nav = (
    <>
      <div className="mb-10 flex h-10 items-center justify-between px-1">
        <Link href="/" aria-label="ProcureAI home">
          <ProcureLogo markClassName="h-8 w-8" />
        </Link>
        <button
          className="md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <nav className="space-y-1" aria-label="Primary navigation">
        {NAV.map((item) => {
          const active =
            pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "group flex h-10 items-center gap-3 px-3 text-[13px] transition-colors",
                active
                  ? "bg-foreground font-medium text-background shadow-sm"
                  : "text-muted-foreground hover:bg-muted/80 hover:text-foreground",
              )}
              style={{ borderRadius: "calc(var(--radius) - 2px)" }}
            >
              <Icon className="h-4 w-4" strokeWidth={1.7} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto border-t border-border pt-5">
        <div className="mb-4 flex items-center gap-2 px-3 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
          Demo environment
        </div>
        <button
          className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
          onClick={() => {
            localStorage.removeItem("procureai_token");
            router.push("/login");
          }}
        >
          <span className="grid h-8 w-8 place-items-center rounded-full bg-muted text-xs font-semibold">
            AB
          </span>
          <span className="min-w-0">
            <span className="block truncate text-xs font-medium">Avery Buyer</span>
            <span className="block text-[10px] text-muted-foreground">Sign out</span>
          </span>
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[15.5rem] flex-col border-r border-border/80 bg-card/95 p-5 backdrop-blur-sm md:flex">
        {nav}
      </aside>
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.button
              aria-label="Close navigation overlay"
              className="fixed inset-0 z-40 bg-foreground/25 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-card p-5 md:hidden"
              initial={{ x: -288 }}
              animate={{ x: 0 }}
              exit={{ x: -288 }}
              transition={{ duration: 0.2 }}
            >
              {nav}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
      <div className="flex min-w-0 flex-1 flex-col md:pl-[15.5rem]">
        <header className="sticky top-0 z-20 flex h-[3.75rem] items-center justify-between border-b border-border/80 bg-background/90 px-4 backdrop-blur-md sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <nav
              className="flex min-w-0 items-center text-xs text-muted-foreground"
              aria-label="Breadcrumb"
            >
              <Link href="/" className="hidden hover:text-foreground sm:block">
                Operations
              </Link>
              {segments.map((segment, index) => (
                <span key={`${segment}-${index}`} className="flex min-w-0 items-center">
                  <ChevronRight className="mx-1 hidden h-3 w-3 sm:block" />
                  <span className="max-w-36 truncate capitalize text-foreground">
                    {segment.replaceAll("-", " ")}
                  </span>
                </span>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              className="hidden h-9 w-52 items-center gap-2 border border-border bg-card px-3 text-xs text-muted-foreground transition-colors hover:border-foreground/30 lg:flex"
              onClick={() => setCommandOpen(true)}
              style={{ borderRadius: "calc(var(--radius) - 2px)" }}
            >
              <Search className="h-3.5 w-3.5" /> Search operations
              <kbd className="ml-auto flex items-center gap-0.5 font-sans">
                <Command className="h-3 w-3" />K
              </kbd>
            </button>
            <button
              className="grid h-9 w-9 place-items-center hover:bg-muted"
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              aria-label="Toggle color theme"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </button>
            <button
              className="relative grid h-9 w-9 place-items-center hover:bg-muted"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-amber-500" />
            </button>
          </div>
        </header>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
      <AnimatePresence>
        {commandOpen && (
          <motion.div
            className="fixed inset-0 z-[60] grid place-items-start bg-foreground/30 px-4 pt-[15vh] backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={() => setCommandOpen(false)}
          >
            <motion.div
              className="w-full max-w-xl overflow-hidden border border-border bg-card shadow-2xl"
              style={{ borderRadius: "var(--radius)" }}
              initial={{ opacity: 0, y: -10, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6 }}
              onMouseDown={(event) => event.stopPropagation()}
            >
              <div className="flex items-center gap-3 border-b border-border px-4">
                <Search className="h-4 w-4 text-muted-foreground" />
                <input
                  autoFocus
                  className="h-14 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                  placeholder="Search cases, POs, suppliers, agent runs…"
                  aria-label="Global search"
                />
                <kbd className="text-xs text-muted-foreground">ESC</kbd>
              </div>
              <div className="p-2">
                <p className="eyebrow px-3 py-2">Quick navigation</p>
                {NAV.slice(0, 5).map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setCommandOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 text-sm hover:bg-muted"
                  >
                    <item.icon className="h-4 w-4 text-muted-foreground" /> {item.label}
                  </Link>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
