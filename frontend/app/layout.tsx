import type { Metadata } from "next";
import "./globals.css";
import { Shell } from "@/components/Shell";
import { I18nProvider } from "@/components/I18nProvider";

export const metadata: Metadata = {
  title: "AgentOS Lite",
  description: "Self-hosted AI workspace with RAG, memory, tools, approvals, LLMOps, and codebase intelligence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          <Shell>{children}</Shell>
        </I18nProvider>
      </body>
    </html>
  );
}
