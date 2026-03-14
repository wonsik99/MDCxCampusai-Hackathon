"use client";

import React from "react";

import { StarJar, StarJarUpdate } from "@/lib/types";

type StarJarOverviewProps = {
  currentJar: StarJar | null;
  history: StarJar[];
  rewardSummary?: StarJarUpdate | null;
  showHistory?: boolean;
};

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

function JarVisualization({ currentJar }: { currentJar: StarJar | null }) {
  const fillHeight = currentJar ? Math.max(currentJar.fill_ratio * 100, currentJar.earned_stars > 0 ? 12 : 0) : 0;

  return (
    <div className="mx-auto w-full max-w-[220px]">
      <div className="relative mx-auto h-[252px] w-[164px] rounded-[2.75rem_2.75rem_1.6rem_1.6rem] border border-white/12 bg-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
        <div className="absolute inset-x-9 top-4 h-4 rounded-full border border-white/10 bg-white/[0.05]" />
        <div className="absolute inset-x-4 bottom-4 overflow-hidden rounded-[2rem_2rem_1.1rem_1.1rem] border border-white/8 bg-white/[0.02]">
          <div
            className="absolute inset-x-0 bottom-0 bg-[linear-gradient(180deg,rgba(214,167,113,0.88),rgba(244,225,192,0.96))] transition-[height] duration-500 ease-out"
            style={{ height: `${fillHeight}%` }}
          />
          <div className="relative flex h-[210px] flex-col items-center justify-between px-4 py-5 text-center">
            <div>
              <p className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">This week</p>
              <p className="mt-2 text-sm font-medium text-[var(--text-strong)]">
                {currentJar ? `${currentJar.earned_stars} / ${currentJar.capacity_stars}` : "0 / 100"}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-[2.3rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">
                {currentJar ? `${Math.round(currentJar.fill_ratio * 100)}%` : "0%"}
              </p>
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-muted)]">Jar fill</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function StarJarOverview({
  currentJar,
  history,
  rewardSummary = null,
  showHistory = true
}: StarJarOverviewProps) {
  const archivedJars = history.filter((jar) => !jar.is_current);

  return (
    <section className="surface p-6 sm:p-8">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr),220px] xl:items-center">
        <div>
          <p className="eyebrow">{rewardSummary ? "Study reward" : "Weekly star jar"}</p>
          <h2 className="section-title mt-3">
            {currentJar ? formatWeekRange(currentJar.week_start_date, currentJar.week_end_date) : "No current jar yet"}
          </h2>
          <p className="plain-note mt-4 max-w-2xl">
            {currentJar
              ? "Active quiz time adds base stars. Accuracy adds a bonus, so careful sessions fill the jar faster."
              : "Finish a quiz session to start filling this week's jar with study stars."}
          </p>

          {rewardSummary ? (
            <div className="surface-muted mt-6 p-4" data-testid="star-jar-reward">
              <p className="text-sm font-semibold text-[var(--text-strong)]">
                You earned {rewardSummary.stars_awarded} stars this session.
              </p>
              <p className="plain-note mt-2">
                {formatStudyTime(rewardSummary.study_time_ms)} of active quiz time at{" "}
                {Math.round(rewardSummary.accuracy_ratio * 100)}% accuracy.
              </p>
            </div>
          ) : null}

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="surface-muted p-4">
              <p className="eyebrow">Stars</p>
              <p className="mt-2 text-2xl font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                {currentJar ? `${currentJar.earned_stars} / ${currentJar.capacity_stars}` : "0 / 100"}
              </p>
            </div>
            <div className="surface-muted p-4">
              <p className="eyebrow">Active quiz time</p>
              <p className="mt-2 text-2xl font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                {currentJar ? formatStudyTime(currentJar.study_time_ms) : "0 sec"}
              </p>
            </div>
            <div className="surface-muted p-4">
              <p className="eyebrow">Sessions</p>
              <p className="mt-2 text-2xl font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                {currentJar?.sessions_count ?? 0}
              </p>
            </div>
            <div className="surface-muted p-4">
              <p className="eyebrow">Weekly accuracy</p>
              <p className="mt-2 text-2xl font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                {currentJar ? `${Math.round(currentJar.average_accuracy * 100)}%` : "0%"}
              </p>
            </div>
          </div>
        </div>

        <JarVisualization currentJar={currentJar} />
      </div>

      {showHistory ? (
        <div className="plain-section mt-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Archive</p>
              <h3 className="mt-3 text-2xl font-medium tracking-[-0.05em] text-[var(--text-strong)]">Past weekly jars</h3>
            </div>
            <p className="text-sm text-[var(--text-muted)]">{archivedJars.length} archived weeks</p>
          </div>

          {archivedJars.length > 0 ? (
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {archivedJars.map((jar) => (
                <article className="surface-muted p-4" key={jar.jar_id}>
                  <p className="eyebrow">{formatWeekRange(jar.week_start_date, jar.week_end_date)}</p>
                  <p className="mt-3 text-xl font-medium tracking-[-0.05em] text-[var(--text-strong)]">
                    {jar.earned_stars} stars
                  </p>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.08]">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,rgba(214,167,113,0.92),rgba(244,225,192,0.98))]"
                      style={{ width: `${Math.max(jar.fill_ratio * 100, jar.earned_stars > 0 ? 10 : 0)}%` }}
                    />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-4 text-sm text-[var(--text-muted)]">
                    <span>{formatStudyTime(jar.study_time_ms)}</span>
                    <span>{Math.round(jar.average_accuracy * 100)}% accuracy</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="plain-note mt-5" data-testid="star-jar-empty-history">
              No archived jars yet.
            </p>
          )}
        </div>
      ) : null}
    </section>
  );
}
