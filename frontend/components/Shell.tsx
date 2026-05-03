"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Bot, Brain, Code2, Database, FileText, Home, Settings, Wrench } from "lucide-react";
import type { ReactNode } from "react";
import { useI18n } from "@/components/I18nProvider";

const nav = [
  { href: "/", labelKey: "overview", icon: Home },
  { href: "/chat", labelKey: "chat", icon: Bot },
  { href: "/documents", labelKey: "documents", icon: FileText },
  { href: "/memory", labelKey: "memory", icon: Brain },
  { href: "/tools", labelKey: "tools", icon: Wrench },
  { href: "/codebase", labelKey: "codebase", icon: Code2 },
  { href: "/llmops", labelKey: "llmops", icon: Activity },
  { href: "/settings", labelKey: "settings", icon: Settings },
] as const;

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { locale, setLocale, t } = useI18n();
  return (
    <div className="min-h-screen bg-paper">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white/80 px-4 py-5 backdrop-blur lg:block">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-ink text-white">
            <Database size={20} />
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-wide text-moss">AgentOS Lite</div>
            <div className="text-xs text-ink/60">{t("productSubtitle")}</div>
          </div>
        </div>
        <div className="mb-5 grid grid-cols-2 rounded border border-line p-1 text-xs">
          <button onClick={() => setLocale("en")} className={`rounded px-2 py-1 ${locale === "en" ? "bg-ink text-white" : "text-ink/60"}`}>EN</button>
          <button onClick={() => setLocale("zh")} className={`rounded px-2 py-1 ${locale === "zh" ? "bg-ink text-white" : "text-ink/60"}`}>中文</button>
        </div>
        <nav className="space-y-1">
          {nav.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded px-3 py-2 text-sm transition ${active ? "bg-ink text-white" : "text-ink/72 hover:bg-line/50 hover:text-ink"}`}
              >
                <Icon size={17} />
                {t(item.labelKey)}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-paper/90 px-5 py-4 backdrop-blur lg:hidden">
          <div className="font-semibold">AgentOS Lite</div>
          <div className="mt-2 inline-grid grid-cols-2 rounded border border-line p-1 text-xs">
            <button onClick={() => setLocale("en")} className={`rounded px-2 py-1 ${locale === "en" ? "bg-ink text-white" : "text-ink/60"}`}>EN</button>
            <button onClick={() => setLocale("zh")} className={`rounded px-2 py-1 ${locale === "zh" ? "bg-ink text-white" : "text-ink/60"}`}>中文</button>
          </div>
          <div className="mt-3 flex gap-2 overflow-x-auto">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className="whitespace-nowrap rounded border border-line px-3 py-1 text-xs">
                {t(item.labelKey)}
              </Link>
            ))}
          </div>
        </header>
        <div className="mx-auto max-w-7xl px-5 py-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
