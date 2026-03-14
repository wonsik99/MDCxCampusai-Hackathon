"use client";

// The shell keeps demo-user state, navigation, and Unity handoff context visible across the app.

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

function getPageMeta(pathname: string) {
  if (pathname.startsWith("/upload")) {
    return { label: "Ingestion", title: "Lecture intake and AI processing" };
  }
  if (pathname.startsWith("/lectures/")) {
    return { label: "Lecture Detail", title: "Summary, concepts, and quiz preparation" };
  }
  if (pathname.startsWith("/dashboard")) {
    return { label: "Analytics", title: "Concept mastery and learner risk signals" };
  }
  if (pathname.startsWith("/recommendations")) {
    return { label: "Recommendations", title: "Ordered next steps from prerequisite logic" };
  }
  if (pathname.startsWith("/quiz/")) {
    return { label: "Quiz Session", title: "Server-graded practice and feedback" };
  }
  return { label: "Overview", title: "Adaptive study support for struggling learners" };
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { selectedUser, users, setSelectedUserId, loading, error } = useUserContext();
  const pageMeta = getPageMeta(pathname);

  return (
    <div className="min-h-screen">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.12] bg-[rgba(42,36,31,0.56)] shadow-[0_18px_45px_rgba(10,6,4,0.14)] backdrop-blur-2xl">
        <div className="mx-auto max-w-[1560px] px-4 xl:px-6">
          <div className="flex flex-wrap items-center gap-3 py-3 lg:flex-nowrap lg:justify-between">
            <div className="flex min-w-0 items-center gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-white/20 bg-white/10 text-[0.75rem] font-semibold uppercase tracking-[0.16em] text-[var(--text-strong)] shadow-[inset_0_1px_0_rgba(255,255,255,0.14)] backdrop-blur-xl">
                SS
              </div>
              <div className="min-w-0">
                <p className="eyebrow">StruggleSense</p>
                <p className="mt-1 truncate text-[1rem] font-medium tracking-[-0.05em] text-[var(--text-strong)]">
                  Learn where the struggle starts.
                </p>
              </div>
            </div>

            <nav
              aria-label="Primary navigation"
              className="order-3 flex w-full gap-2 overflow-x-auto pb-1 lg:order-none lg:w-auto lg:flex-1 lg:justify-center lg:pb-0"
            >
              {NAV_ITEMS.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    className={`shrink-0 rounded-full border px-4 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.12em] transition ${
                      active
                        ? "border-white/[0.24] bg-white/[0.14] text-[var(--text-strong)] shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]"
                        : "border-white/10 bg-white/[0.04] text-[var(--text-muted)] hover:border-white/[0.18] hover:bg-white/[0.07] hover:text-[var(--text-strong)]"
                    }`}
                    href={item.href}
                    key={item.href}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="ml-auto flex items-center gap-3 lg:ml-0">
              <span className="badge hidden lg:inline-flex">Study system</span>
              <div className="hidden text-right lg:block">
                <p className="eyebrow">Active learner</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  {selectedUser?.name ?? "Select learner"}
                </p>
              </div>
              <select
                className="field-select w-[170px] min-w-0 !min-h-[44px] !px-3 !py-2 text-sm lg:w-[220px]"
                disabled={loading}
                onChange={(event) => setSelectedUserId(event.target.value)}
                value={selectedUser?.id ?? ""}
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {error ? <p className="pb-3 text-sm text-red-300">{error}</p> : null}
        </div>
      </header>

      <div className="mx-auto max-w-[1560px] px-4 pb-10 pt-[152px] xl:px-6 lg:pt-[110px]">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr),300px]">
          <div className="space-y-8">
            <header className="border-b border-white/[0.12] pb-5">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="eyebrow">{pageMeta.label}</p>
                  <h2 className="mt-3 text-[clamp(1.7rem,2.2vw,2.7rem)] font-medium leading-[0.96] tracking-[-0.06em] text-[var(--text-strong)]">
                    {pageMeta.title}
                  </h2>
                </div>
                <p className="text-sm text-[var(--text-muted)]">Server graded</p>
              </div>
            </header>

            <main>{children}</main>
          </div>

          <aside className="space-y-8 border-t border-white/[0.12] pt-6 xl:sticky xl:top-[106px] xl:h-fit xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
            <section>
              <LectureSidebar userId={selectedUser?.id ?? null} />
            </section>

            <section className="plain-section">
              <p className="eyebrow">Unity integration</p>
              <p className="plain-note mt-3">Web and Unity use the same quiz endpoints.</p>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
