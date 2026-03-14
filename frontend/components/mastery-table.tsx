"use client";

import { groupMasteryByLecture } from "@/lib/analytics";
import { ConceptMasteryRead } from "@/lib/types";

function scoreToClass(score: number) {
  if (score < 0.6) return "bg-ember/15 text-ember";
  if (score < 0.75) return "bg-clay/15 text-clay";
  return "bg-moss/15 text-moss";
}

export function MasteryTable({ masteries }: { masteries: ConceptMasteryRead[] }) {
  const grouped = groupMasteryByLecture(masteries);

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([lectureTitle, lectureMasteries]) => (
        <section className="rounded-[28px] border border-ink/10 bg-white/80 p-6 shadow-glow" key={lectureTitle}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-semibold text-ink">{lectureTitle}</h3>
            <p className="text-xs uppercase tracking-[0.18em] text-ink/50">
              {lectureMasteries.filter((item) => item.is_weak).length} weak concepts
            </p>
          </div>
          <div className="space-y-3">
            {lectureMasteries.map((mastery) => (
              <div
                className="grid gap-3 rounded-2xl border border-ink/8 bg-mist/45 p-4 md:grid-cols-[1.6fr,0.8fr,0.7fr,0.7fr]"
                key={mastery.concept_id}
              >
                <div>
                  <p className="font-medium text-ink">{mastery.concept_name}</p>
                  <p className="text-sm text-ink/65">{mastery.concept_slug}</p>
                </div>
                <div className="flex items-center">
                  <span className={`rounded-full px-3 py-1 text-sm font-semibold ${scoreToClass(mastery.mastery_score)}`}>
                    {(mastery.mastery_score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm text-ink/70">Correct: {mastery.correct_count}</p>
                <p className="text-sm text-ink/70">Wrong: {mastery.wrong_count}</p>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
