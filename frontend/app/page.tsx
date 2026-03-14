"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { getConceptMastery, getRecommendations, listLectures } from "@/lib/api";
import { ConceptMasteryRead, LectureListItem, Recommendation } from "@/lib/types";

export default function HomePage() {
  const { selectedUser } = useUserContext();
  const [lectures, setLectures] = useState<LectureListItem[]>([]);
  const [masteries, setMasteries] = useState<ConceptMasteryRead[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    void Promise.all([
      listLectures(selectedUser.id),
      getConceptMastery(selectedUser.id),
      getRecommendations(selectedUser.id)
    ]).then(([lectureData, masteryData, recommendationData]) => {
      setLectures(lectureData);
      setMasteries(masteryData);
      setRecommendations(recommendationData.recommendations);
    });
  }, [selectedUser]);

  const weakConcepts = useMemo(() => masteries.filter((item) => item.is_weak), [masteries]);
  const latestLecture = lectures[0] ?? null;
  const nextRecommendation = recommendations[0] ?? null;

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Overview</p>
        <h1 className="mt-4 max-w-5xl text-[clamp(1.8rem,3.2vw,3rem)] font-medium leading-[0.98] tracking-[-0.05em] text-[var(--text-strong)]">
          Study state, quickly.
        </h1>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link className="btn-primary" href="/upload">
            Upload
          </Link>
          <Link className="btn-secondary" href="/dashboard">
            Analytics
          </Link>
        </div>

        <div className="plain-strip mt-8 grid gap-0 md:grid-cols-4">
          <div className="py-4 md:py-5 md:pr-6">
            <p className="eyebrow">Learner</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
              {selectedUser?.name ?? "Not selected"}
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:px-6 md:py-5">
            <p className="eyebrow">Lectures</p>
            <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{lectures.length}</p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:px-6 md:py-5">
            <p className="eyebrow">Weak</p>
            <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{weakConcepts.length}</p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:pl-6 md:py-5">
            <p className="eyebrow">Recommendations</p>
            <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">{recommendations.length}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-10 xl:grid-cols-[minmax(0,1fr),minmax(320px,0.92fr)]">
        <div className="space-y-10">
          <section className="plain-section">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="eyebrow">Needs attention</p>
                <h2 className="section-title mt-3">Weak concepts</h2>
              </div>
              <Link className="editorial-link" href="/recommendations">
                Recommendations
              </Link>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {weakConcepts.length > 0 ? (
                weakConcepts.slice(0, 8).map((concept) => (
                  <span className="badge-primary" key={concept.concept_id}>
                    {concept.concept_name}
                  </span>
                ))
              ) : (
                <p className="plain-note">No weak concepts.</p>
              )}
            </div>
          </section>

          <section className="plain-section">
            <p className="eyebrow">Latest lecture</p>
            <h2 className="section-title mt-3">{latestLecture?.title ?? "No lecture"}</h2>
            <div className="mt-5 flex flex-wrap gap-3 text-sm text-[var(--text-muted)]">
              {latestLecture ? (
                <>
                  <span>{latestLecture.concept_count} concepts</span>
                  <span>{latestLecture.question_count} questions</span>
                </>
              ) : (
                <span>Upload a lecture to start.</span>
              )}
            </div>
            {latestLecture ? (
              <Link className="editorial-link mt-6" href={`/lectures/${latestLecture.id}`}>
                Open lecture
              </Link>
            ) : null}
          </section>
        </div>

        <section className="plain-section xl:pt-0 xl:border-t-0">
          <p className="eyebrow">Next recommendation</p>
          <h2 className="section-title mt-3">{nextRecommendation?.title ?? "No recommendation"}</h2>
          {nextRecommendation?.message ? <p className="plain-note mt-4">{nextRecommendation.message}</p> : null}
        </section>
      </section>
    </div>
  );
}
