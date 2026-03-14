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
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="eyebrow">Lecture library</p>
        </div>
        <Link className="editorial-link" href="/upload">
          Upload
        </Link>
      </div>

      {error ? <p className="mb-3 text-sm text-red-300">{error}</p> : null}

      <div className="divide-y divide-white/10">
        {lectures.length === 0 ? (
          <div className="empty-state text-sm leading-7">
            No lectures yet. Upload one to create the first concept map.
          </div>
        ) : null}

        {lectures.map((lecture) => (
          <Link
            className="block py-4 transition hover:text-white"
            href={`/lectures/${lecture.id}`}
            key={lecture.id}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold tracking-[-0.03em] text-[var(--text-strong)]">{lecture.title}</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  {lecture.concept_count} concepts • {lecture.question_count} questions
                </p>
              </div>
              <span className="badge">{lecture.source_type}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
