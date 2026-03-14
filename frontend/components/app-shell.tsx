"use client";

// The shell keeps demo-user state, lecture navigation, and Unity handoff messaging visible everywhere.

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { LectureSidebar } from "@/components/lecture-sidebar";
import { useUserContext } from "@/components/user-context";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/dashboard", label: "Analytics" },
  { href: "/recommendations", label: "Recommendations" }
] satisfies Array<{ href: Route; label: string }>;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { selectedUser, users, setSelectedUserId, loading, error } = useUserContext();

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(221,143,85,0.2),_transparent_28%),linear-gradient(135deg,_#f7f1e3_0%,_#dde5df_55%,_#f8f5ef_100%)] text-ink">
      <div className="mx-auto grid min-h-screen max-w-7xl gap-8 px-6 py-8 lg:grid-cols-[320px,1fr]">
        <div className="space-y-6">
          <div className="rounded-[32px] bg-ink p-6 text-sand shadow-glow">
            <p className="text-xs uppercase tracking-[0.28em] text-sand/70">StruggleSense</p>
            <h1 className="mt-4 text-3xl font-semibold leading-tight">AI study support for the concepts learners miss first.</h1>
            <p className="mt-3 text-sm leading-6 text-sand/75">
              Upload lecture material, generate concept-tagged quizzes, track mastery, and recommend the next study step in prerequisite order.
            </p>
            <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-sand/60">Active student</p>
              <select
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-sand outline-none"
                disabled={loading}
                onChange={(event) => setSelectedUserId(event.target.value)}
                value={selectedUser?.id ?? ""}
              >
                {users.map((user) => (
                  <option className="text-ink" key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
              {error ? <p className="mt-2 text-sm text-[#ffb4a8]">{error}</p> : null}
            </div>
          </div>

          <nav className="rounded-[28px] border border-ink/10 bg-white/70 p-4 shadow-glow">
            <div className="flex flex-wrap gap-2">
              {NAV_ITEMS.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                      active ? "bg-clay text-white" : "bg-mist text-ink hover:bg-white"
                    }`}
                    href={item.href}
                    key={item.href}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </nav>

          <LectureSidebar userId={selectedUser?.id ?? null} />

          <div className="rounded-[28px] border border-moss/20 bg-moss p-5 text-white shadow-glow">
            <p className="text-xs uppercase tracking-[0.24em] text-white/70">Unity Integration</p>
            <p className="mt-3 text-sm leading-6 text-white/85">
              Unity should call the same quiz session and recommendation endpoints shown here. The web quiz is only a thin demo client over those backend contracts.
            </p>
          </div>
        </div>

        <main className="pb-10">{children}</main>
      </div>
    </div>
  );
}
