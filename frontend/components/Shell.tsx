"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Bot, Brain, CheckSquare, Code2, Database, FileText, Home, Settings, Wrench } from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/chat", label: "Chat", icon: Bot },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/tools", label: "Tools", icon: Wrench },
  { href: "/codebase", label: "Codebase", icon: Code2 },
  { href: "/llmops", label: "LLMOps", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-paper">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white/80 px-4 py-5 backdrop-blur lg:block">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-ink text-white">
            <Database size={20} />
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-wide text-moss">AgentOS Lite</div>
            <div className="text-xs text-ink/60">Self-hosted AI workspace</div>
          </div>
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
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-paper/90 px-5 py-4 backdrop-blur lg:hidden">
          <div className="font-semibold">AgentOS Lite</div>
          <div className="mt-3 flex gap-2 overflow-x-auto">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className="whitespace-nowrap rounded border border-line px-3 py-1 text-xs">
                {item.label}
              </Link>
            ))}
          </div>
        </header>
        <div className="mx-auto max-w-7xl px-5 py-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}

