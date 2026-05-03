import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 border-b border-line pb-5 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-3xl font-semibold text-ink">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-ink/65">{subtitle}</p>
      </div>
      {actions}
    </div>
  );
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded border border-line bg-white p-4 shadow-soft ${className}`}>{children}</section>;
}

export function Stat({ label, value, tone = "moss" }: { label: string; value: string | number; tone?: "moss" | "aqua" | "clay" }) {
  const colors = { moss: "text-moss", aqua: "text-aqua", clay: "text-clay" };
  return (
    <div className="rounded border border-line bg-white p-4">
      <div className="text-xs uppercase tracking-wide text-ink/50">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${colors[tone]}`}>{value}</div>
    </div>
  );
}

export function EmptyState({ text }: { text: string }) {
  return <div className="rounded border border-dashed border-line bg-paper p-4 text-sm text-ink/60">{text}</div>;
}

