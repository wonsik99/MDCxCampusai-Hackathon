"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listLectures } from "@/lib/api";
import { LectureListItem } from "@/lib/types";

export function LectureSidebar({ userId }: { userId: string | null }) {
  const [lectures, setLectures] = useState<LectureListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      return;
    }
    void listLectures(userId)
      .then((items) => {
        setLectures(items);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load lectures."));
  }, [userId]);

  return (
    <aside className="rounded-[28px] border border-ink/10 bg-white/80 p-5 shadow-glow">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-[0.24em] text-ink/60">Lecture Library</h2>
        <Link className="text-sm font-medium text-clay" href="/upload">
          Upload
        </Link>
      </div>
      {error ? <p className="text-sm text-ember">{error}</p> : null}
      <div className="space-y-3">
        {lectures.length === 0 ? (
          <div className="rounded-2xl bg-sand p-4 text-sm text-ink/70">
            No lectures yet. Upload one to generate concepts and quiz content.
          </div>
        ) : null}
        {lectures.map((lecture) => (
          <Link
            className="block rounded-2xl border border-ink/8 bg-mist/50 p-4 transition hover:border-clay/40 hover:bg-white"
            key={lecture.id}
            href={`/lectures/${lecture.id}`}
          >
            <p className="font-semibold text-ink">{lecture.title}</p>
            <p className="mt-1 text-sm text-ink/65">
              {lecture.concept_count} concepts • {lecture.question_count} questions
            </p>
          </Link>
        ))}
      </div>
    </aside>
  );
}
