"use client";

import { groupMasteryByLecture } from "@/lib/analytics";
import { ConceptMasteryRead } from "@/lib/types";

function scoreToClass(score: number) {
  if (score < 0.6) return "bg-[rgba(209,165,124,0.16)] text-[#f7d8b8]";
  if (score < 0.75) return "bg-white/8 text-[#d9d1c5]";
  return "bg-white text-black";
}

function scoreToBar(score: number) {
  if (score < 0.6) return "bg-[#8c613d]";
  if (score < 0.75) return "bg-[#b8afa2]";
  return "bg-white";
}

export function MasteryTable({ masteries }: { masteries: ConceptMasteryRead[] }) {
  const grouped = groupMasteryByLecture(masteries);

  return (
    <div className="space-y-10">
      {Object.entries(grouped).map(([lectureTitle, lectureMasteries]) => (
        <section className="plain-section" key={lectureTitle}>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Lecture</p>
              <h3 className="mt-3 text-[1.45rem] font-medium leading-tight tracking-[-0.05em] text-[var(--text-strong)]">
                {lectureTitle}
              </h3>
            </div>
            <p className="text-sm text-[var(--text-muted)]">
              {lectureMasteries.filter((item) => item.is_weak).length} weak
            </p>
          </div>

          <div className="mt-6 divide-y divide-white/10">
            {lectureMasteries.map((mastery) => (
              <div className="py-4 first:pt-0 last:pb-0" key={mastery.concept_id}>
                <div className="grid gap-4 md:grid-cols-[1.8fr,0.7fr,0.7fr,0.7fr] md:items-center">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="font-semibold tracking-[-0.03em] text-[var(--text-strong)]">{mastery.concept_name}</p>
                      {mastery.is_weak ? <span className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-[#f7d8b8]">Weak</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-[var(--text-muted)]">{mastery.concept_slug}</p>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                      <div
                        className={`h-full rounded-full ${scoreToBar(mastery.mastery_score)}`}
                        style={{ width: `${Math.max(mastery.mastery_score * 100, 6)}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex md:justify-center">
                    <span className={`rounded-full px-3 py-1 text-sm font-semibold ${scoreToClass(mastery.mastery_score)}`}>
                      {(mastery.mastery_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-[var(--text-muted)]">Correct {mastery.correct_count}</p>
                  <p className="text-sm text-[var(--text-muted)]">Wrong {mastery.wrong_count}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
