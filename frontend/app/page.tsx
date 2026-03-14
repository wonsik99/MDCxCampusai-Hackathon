"use client";

import Link from "next/link";

import { useUserContext } from "@/components/user-context";

export default function HomePage() {
  const { selectedUser } = useUserContext();

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[40px] border border-ink/10 bg-white/75 p-8 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-clay">Production-style MVP</p>
        <h2 className="mt-4 text-5xl font-semibold leading-tight text-ink" style={{ fontFamily: "var(--font-heading)" }}>
          Turn lecture files into concept-level learning diagnostics.
        </h2>
        <p className="mt-5 max-w-3xl text-lg leading-8 text-ink/75">
          StruggleSense is built to go beyond flashcards. It transforms lecture material into active quiz play, stores answer history, detects weak concepts and prerequisite gaps, and recommends what the learner should study next.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link className="rounded-full bg-clay px-5 py-3 text-sm font-semibold text-white" href="/upload">
            Upload a lecture
          </Link>
          <Link className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-sand" href="/dashboard">
            View analytics
          </Link>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {[
          {
            title: "1. Content understanding",
            copy: "PDF or raw text is cleaned, summarized, concept-tagged, and prepared for structured quiz generation."
          },
          {
            title: "2. Gameplay analytics",
            copy: "Server-side grading updates mastery per concept and flags repeated recent mistakes deterministically."
          },
          {
            title: "3. Ordered study guidance",
            copy: "Recommendations are sorted in prerequisite-aware order so the learner revisits the blocking concept first."
          }
        ].map((item) => (
          <article className="rounded-[28px] border border-ink/10 bg-white/80 p-6 shadow-glow" key={item.title}>
            <h3 className="text-xl font-semibold text-ink">{item.title}</h3>
            <p className="mt-3 text-sm leading-7 text-ink/70">{item.copy}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.4fr,1fr]">
        <article className="rounded-[32px] border border-ink/10 bg-ink p-7 text-sand shadow-glow">
          <p className="text-xs uppercase tracking-[0.22em] text-sand/65">Current demo student</p>
          <h3 className="mt-3 text-2xl font-semibold">{selectedUser?.name ?? "Select a student from the sidebar"}</h3>
          <p className="mt-3 text-sm leading-7 text-sand/75">
            The web app identifies the active learner with <code>X-User-Id</code>, mirroring how a future auth layer can resolve the current user without changing lecture or quiz routes.
          </p>
        </article>
        <article className="rounded-[32px] border border-ink/10 bg-white/80 p-7 shadow-glow">
          <p className="text-xs uppercase tracking-[0.22em] text-moss">Unity handoff</p>
          <h3 className="mt-3 text-2xl font-semibold text-ink">Thin client by design</h3>
          <p className="mt-3 text-sm leading-7 text-ink/70">
            Unity will later call <code>/quiz-sessions/start</code>, <code>/questions</code>, <code>/submit-answer</code>, <code>/finish</code>, and <code>/users/:id/recommendations</code>. No gameplay rules are implemented in the browser.
          </p>
        </article>
      </section>
    </div>
  );
}
