"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MasteryTable } from "@/components/mastery-table";
import { StarJarOverview } from "@/components/star-jar-overview";
import { useUserContext } from "@/components/user-context";
import { getWeakConcepts } from "@/lib/analytics";
import { getConceptMastery, getStarJars } from "@/lib/api";
import { ConceptMasteryRead, StarJar } from "@/lib/types";

export default function DashboardPage() {
  const { selectedUser } = useUserContext();
  const [masteries, setMasteries] = useState<ConceptMasteryRead[]>([]);
  const [currentJar, setCurrentJar] = useState<StarJar | null>(null);
  const [jarHistory, setJarHistory] = useState<StarJar[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    void Promise.all([getConceptMastery(selectedUser.id), getStarJars(selectedUser.id)])
      .then(([masteryData, starJarData]) => {
        setMasteries(masteryData);
        setCurrentJar(starJarData.current_jar);
        setJarHistory(starJarData.history);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load dashboard analytics."));
  }, [selectedUser]);

  const weakConcepts = getWeakConcepts(masteries);
  const stableConcepts = masteries.filter((item) => item.mastery_score >= 0.75).length;

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Momentum + mastery</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(1.8rem,3.2vw,3rem)] font-medium leading-[0.98] tracking-[-0.05em] text-[var(--text-strong)]">
          Weekly progress, easy to spot.
        </h1>
      </section>

      <section className="grid gap-8 xl:grid-cols-[minmax(0,1.12fr),minmax(320px,0.88fr)]">
        <StarJarOverview currentJar={currentJar} history={jarHistory} />

        <div className="space-y-8">
          <div className="plain-strip grid gap-0 md:grid-cols-2">
            <div className="py-4 md:py-5 md:pr-6">
              <p className="eyebrow">Learner</p>
              <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
                {selectedUser?.name ?? "Not selected"}
              </p>
            </div>
            <div className="py-4 md:border-l md:border-white/10 md:pl-6 md:py-5">
              <p className="eyebrow">Concepts tracked</p>
              <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{masteries.length}</p>
            </div>
            <div className="py-4 md:border-t md:border-white/10 md:py-5 md:pr-6">
              <p className="eyebrow">Weak concepts</p>
              <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{weakConcepts.length}</p>
            </div>
            <div className="py-4 md:border-l md:border-t md:border-white/10 md:pl-6 md:py-5">
              <p className="eyebrow">Stable concepts</p>
              <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{stableConcepts}</p>
            </div>
          </div>

          <section className="plain-section">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="eyebrow">Needs attention</p>
                <h2 className="section-title mt-3">
                  {weakConcepts.length > 0 ? "Review first" : "No weak concepts"}
                </h2>
              </div>
              {weakConcepts.length > 0 ? (
                <Link className="btn-secondary" href="/recommendations">
                  Review plan
                </Link>
              ) : null}
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {weakConcepts.length > 0 ? (
                weakConcepts.map((concept) => (
                  <span className="badge-primary" key={concept.concept_id}>
                    {concept.concept_name}
                  </span>
                ))
              ) : (
                <div className="text-sm leading-7 text-[var(--text-muted)]">
                  No weak concepts flagged yet.
                </div>
              )}
            </div>
          </section>
        </div>
      </section>

      {error ? <p className="border-t border-red-400/30 pt-4 text-sm text-red-300">{error}</p> : null}

      <section className="space-y-6">
        <div>
          <p className="eyebrow">Lecture breakdown</p>
          <h2 className="section-title mt-3">
            {selectedUser?.name ?? "Learner"} mastery by lecture
          </h2>
        </div>

        {masteries.length === 0 && !error ? (
          <div className="plain-section text-sm leading-7 text-[var(--text-muted)]">
            No mastery data yet.
          </div>
        ) : (
          <MasteryTable masteries={masteries} />
        )}
      </section>
    </div>
  );
}
