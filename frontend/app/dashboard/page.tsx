"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MasteryTable } from "@/components/mastery-table";
import { useUserContext } from "@/components/user-context";
import { getWeakConcepts } from "@/lib/analytics";
import { getConceptMastery } from "@/lib/api";
import { ConceptMasteryRead } from "@/lib/types";

export default function DashboardPage() {
  const { selectedUser } = useUserContext();
  const [masteries, setMasteries] = useState<ConceptMasteryRead[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    void getConceptMastery(selectedUser.id)
      .then((data) => {
        setMasteries(data);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load mastery."));
  }, [selectedUser]);

  const weakConcepts = getWeakConcepts(masteries);

  return (
    <div className="space-y-8">
      <section className="grid gap-6 md:grid-cols-3">
        <article className="rounded-[28px] border border-ink/10 bg-white/80 p-6 shadow-glow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/55">Concept records</p>
          <h2 className="mt-3 text-4xl font-semibold text-ink">{masteries.length}</h2>
        </article>
        <article className="rounded-[28px] border border-ink/10 bg-white/80 p-6 shadow-glow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/55">Weak concepts</p>
          <h2 className="mt-3 text-4xl font-semibold text-ember">{weakConcepts.length}</h2>
        </article>
        <article className="rounded-[28px] border border-ink/10 bg-white/80 p-6 shadow-glow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/55">Next action</p>
          <Link className="mt-4 inline-flex rounded-full bg-clay px-4 py-2 text-sm font-semibold text-white" href="/recommendations">
            Review ordered plan
          </Link>
        </article>
      </section>

      {weakConcepts.length > 0 ? (
        <section className="rounded-[32px] border border-ember/15 bg-white/80 p-6 shadow-glow">
          <p className="text-xs uppercase tracking-[0.2em] text-ember">Detected weak concepts</p>
          <div className="mt-4 flex flex-wrap gap-3">
            {weakConcepts.map((concept) => (
              <span className="rounded-full bg-ember/10 px-4 py-2 text-sm font-medium text-ember" key={concept.concept_id}>
                {concept.concept_name}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {error ? <p className="rounded-2xl bg-white/70 p-4 text-sm text-ember shadow-glow">{error}</p> : null}
      {masteries.length === 0 && !error ? (
        <div className="rounded-[32px] bg-white/70 p-8 text-sm text-ink/70 shadow-glow">
          No mastery data yet. Complete a quiz session to populate analytics.
        </div>
      ) : (
        <MasteryTable masteries={masteries} />
      )}
    </div>
  );
}
