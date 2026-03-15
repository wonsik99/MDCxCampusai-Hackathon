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
    void getRecommendations(selectedUser.id, true)
      .then((data) => {
        setRecommendations(data.recommendations);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load recommendations."));
  }, [selectedUser]);

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Recommendations</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(1.8rem,3.2vw,3rem)] font-medium leading-[0.98] tracking-[-0.05em] text-[var(--text-strong)]">
          What to review next.
        </h1>
        <div className="plain-strip mt-8 py-4">
          <p className="text-sm text-[var(--text-muted)]">{recommendations.length} items</p>
        </div>
      </section>

      {error ? <p className="border-t border-red-400/30 pt-4 text-sm text-red-300">{error}</p> : null}

      <RecommendationList recommendations={recommendations} />
    </div>
  );
}
