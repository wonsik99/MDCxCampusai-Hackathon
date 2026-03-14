"use client";

// The shell keeps demo-user state, navigation, and study momentum visible across the app.

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import { LectureSidebar } from "@/components/lecture-sidebar";
import { useUserContext } from "@/components/user-context";
import { getStarJars } from "@/lib/api";
import { StarJar } from "@/lib/types";

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

function formatWeekRange(start: string, end: string) {
  const formatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
  const [startYear, startMonth, startDay] = start.split("-").map(Number);
  const [endYear, endMonth, endDay] = end.split("-").map(Number);
  return `${formatter.format(new Date(startYear, startMonth - 1, startDay))} - ${formatter.format(
    new Date(endYear, endMonth - 1, endDay)
  )}`;
}

function formatStudyTime(ms: number) {
  if (ms < 60_000) {
    return `${Math.max(1, Math.round(ms / 1000))} sec`;
  }
  const minutes = ms / 60_000;
  return `${minutes >= 10 ? Math.round(minutes) : minutes.toFixed(1)} min`;
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { selectedUser, users, setSelectedUserId, loading, error } = useUserContext();
  const pageMeta = getPageMeta(pathname);
  const [currentJar, setCurrentJar] = useState<StarJar | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      setCurrentJar(null);
      return;
    }

    void getStarJars(selectedUser.id)
      .then((data) => setCurrentJar(data.current_jar))
      .catch(() => setCurrentJar(null));
  }, [selectedUser]);

  return (
    <div className="min-h-screen">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.12] bg-[rgba(42,36,31,0.56)] shadow-[0_18px_45px_rgba(10,6,4,0.14)] backdrop-blur-2xl">
        <div className="mx-auto max-w-[1560px] px-4 xl:px-6">
          <div className="flex flex-wrap items-center gap-3 py-3 lg:flex-nowrap lg:justify-between">
            <div className="flex min-w-0 items-center gap-4">
              <div className="brand-mark" aria-hidden>
                <span className="brand-mark-inner">S</span>
              </div>
              <div className="min-w-0">
                <p className="eyebrow">StruggleSense</p>
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
              <div className="hidden text-right lg:block">
                <p className="eyebrow">Active learner</p>
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
        <div className="grid gap-6 xl:grid-cols-[300px,minmax(0,1fr)]">
          <aside className="sidebar-scrollbar space-y-8 border-t border-white/[0.12] pt-6 xl:sticky xl:top-[106px] xl:max-h-[calc(100vh-130px)] xl:overflow-y-auto xl:border-r xl:border-t-0 xl:pr-6 xl:pt-0">
            <section>
              <LectureSidebar userId={selectedUser?.id ?? null} />
            </section>

            <section className="plain-section">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="eyebrow whitespace-nowrap">Weekly star jar</p>
                  <h3 className="mt-3 text-xl font-medium tracking-[-0.05em] text-[var(--text-strong)]">
                    {currentJar ? `${currentJar.earned_stars} / ${currentJar.capacity_stars} ⭐️` : "No stars yet"}
                  </h3>
                </div>
                <Link className="btn-ghost" href="/dashboard">
                  Dashboard
                </Link>
              </div>

              {currentJar ? (
                <div className="surface-muted mt-5 p-4">
                  <p className="text-sm text-[var(--text-muted)]">
                    {formatWeekRange(currentJar.week_start_date, currentJar.week_end_date)}
                  </p>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.08]">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,rgba(214,167,113,0.92),rgba(244,225,192,0.98))]"
                      style={{ width: `${Math.max(currentJar.fill_ratio * 100, currentJar.earned_stars > 0 ? 10 : 0)}%` }}
                    />
                  </div>
                  <div className="mt-4 grid gap-3 text-sm text-[var(--text-muted)]">
                    <div className="flex items-center justify-between gap-3">
                      <span>Fill</span>
                      <span className="font-medium text-[var(--text-strong)]">
                        {Math.round(currentJar.fill_ratio * 100)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span>Quiz time</span>
                      <span className="font-medium text-[var(--text-strong)]">
                        {formatStudyTime(currentJar.study_time_ms)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span>Accuracy</span>
                      <span className="font-medium text-[var(--text-strong)]">
                        {Math.round(currentJar.average_accuracy * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="plain-note mt-3">
                  Finish a quiz session to start filling this week&apos;s jar.
                </p>
              )}
            </section>
          </aside>

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
        </div>
      </div>
    </div>
  );
}
