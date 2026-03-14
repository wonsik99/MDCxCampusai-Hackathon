"use client";

import { useEffect, useState } from "react";

import { RecommendationList } from "@/components/recommendation-list";
import { useUserContext } from "@/components/user-context";
import { getRecommendations } from "@/lib/api";
import { Recommendation } from "@/lib/types";

export default function RecommendationsPage() {
  const { selectedUser } = useUserContext();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    void getRecommendations(selectedUser.id)
      .then((data) => {
        setRecommendations(data.recommendations);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load recommendations."));
  }, [selectedUser]);

  return (
    <div className="space-y-8">
      <section className="rounded-[36px] border border-ink/10 bg-white/80 p-8 shadow-glow">
        <p className="text-xs uppercase tracking-[0.2em] text-moss">Prerequisite-aware next steps</p>
        <h2 className="mt-3 text-4xl font-semibold text-ink" style={{ fontFamily: "var(--font-heading)" }}>
          Ordered study recommendations
        </h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-ink/70">
          Recommendation order is decided by backend analytics. The model only helps phrase the action clearly after weak concepts and prerequisite gaps have been chosen deterministically.
        </p>
      </section>
      {error ? <p className="rounded-2xl bg-white/70 p-4 text-sm text-ember shadow-glow">{error}</p> : null}
      <RecommendationList recommendations={recommendations} />
    </div>
  );
}
