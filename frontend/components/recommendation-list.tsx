"use client";

import React from "react";

import { Recommendation } from "@/lib/types";

export function RecommendationList({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) {
    return (
      <div className="plain-section text-sm leading-7 text-[var(--text-muted)]">
        No recommendations yet.
      </div>
    );
  }

  return (
    <div className="divide-y divide-white/10">
      {recommendations.map((recommendation) => (
        <article className="grid gap-4 py-5 md:grid-cols-[56px,1fr]" key={recommendation.recommendation_id}>
          <div className="text-[1.45rem] font-medium tracking-[-0.06em] text-[var(--text-strong)]">
            {recommendation.rank}
          </div>

          <div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-[1.25rem] font-medium leading-tight tracking-[-0.05em] text-[var(--text-strong)]">
                {recommendation.title}
              </h3>
              <span className="text-[0.72rem] uppercase tracking-[0.12em] text-[var(--text-muted)]">
                {recommendation.reason_code.replaceAll("_", " ")}
              </span>
            </div>
            <p className="plain-note mt-3">{recommendation.message}</p>
            {recommendation.lecture_title ? (
              <p className="mt-3 text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">
                {recommendation.lecture_title}
              </p>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}
