"use client";

import React from "react";

import { Recommendation } from "@/lib/types";

export function RecommendationList({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) {
    return (
      <div className="rounded-[28px] border border-dashed border-ink/20 bg-white/70 p-6 text-sm text-ink/70">
        Recommendations will appear after the learner has answer history.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {recommendations.map((recommendation) => (
        <article
          className="rounded-[28px] border border-ink/10 bg-white/85 p-6 shadow-glow"
          key={recommendation.recommendation_id}
        >
          <div className="mb-3 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">
                Step {recommendation.rank}
              </p>
              <h3 className="mt-1 text-xl font-semibold text-ink">{recommendation.title}</h3>
            </div>
            <span className="rounded-full bg-sand px-3 py-1 text-xs font-medium text-ink/70">
              {recommendation.reason_code.replaceAll("_", " ")}
            </span>
          </div>
          <p className="text-sm leading-7 text-ink/75">{recommendation.message}</p>
          {recommendation.lecture_title ? (
            <p className="mt-3 text-xs uppercase tracking-[0.18em] text-ink/50">
              Lecture: {recommendation.lecture_title}
            </p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
