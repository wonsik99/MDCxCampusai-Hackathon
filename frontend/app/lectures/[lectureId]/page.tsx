"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { generateQuiz, getLecture, startQuizSession } from "@/lib/api";
import { LectureDetail, QuizGenerationResponse } from "@/lib/types";

export default function LectureDetailPage() {
  const params = useParams<{ lectureId: string }>();
  const router = useRouter();
  const { selectedUser } = useUserContext();
  const [lecture, setLecture] = useState<LectureDetail | null>(null);
  const [generationResult, setGenerationResult] = useState<QuizGenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    setLoading(true);
    void getLecture(selectedUser.id, params.lectureId)
      .then((data) => {
        setLecture(data);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load lecture."))
      .finally(() => setLoading(false));
  }, [params.lectureId, selectedUser]);

  async function handleGenerateQuiz() {
    if (!selectedUser || !lecture) return;
    setWorking(true);
    try {
      const response = await generateQuiz(selectedUser.id, lecture.id);
      setGenerationResult(response);
      const refreshed = await getLecture(selectedUser.id, lecture.id);
      setLecture(refreshed);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Quiz generation failed.");
    } finally {
      setWorking(false);
    }
  }

  async function handleStartQuiz() {
    if (!selectedUser || !lecture) return;
    setWorking(true);
    try {
      const session = await startQuizSession(selectedUser.id, lecture.id);
      router.push(`/quiz/${session.session_id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to start quiz.");
      setWorking(false);
    }
  }

  if (loading) {
    return <div className="rounded-[32px] bg-white/70 p-8 shadow-glow">Loading lecture...</div>;
  }

  if (!lecture) {
    return <div className="rounded-[32px] bg-white/70 p-8 shadow-glow">Lecture not found.</div>;
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[36px] border border-ink/10 bg-white/80 p-8 shadow-glow">
        <p className="text-xs uppercase tracking-[0.24em] text-clay">{lecture.source_type.toUpperCase()} lecture</p>
        <h2 className="mt-3 text-4xl font-semibold text-ink" style={{ fontFamily: "var(--font-heading)" }}>
          {lecture.title}
        </h2>
        <p className="mt-5 text-base leading-8 text-ink/75">{lecture.summary_block.summary}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="rounded-full bg-clay px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
            disabled={working}
            onClick={handleGenerateQuiz}
            type="button"
          >
            {lecture.quiz_generated ? "Regenerate quiz" : "Generate quiz"}
          </button>
          <button
            className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-sand disabled:opacity-50"
            disabled={working || !lecture.quiz_generated}
            onClick={handleStartQuiz}
            type="button"
          >
            Start web quiz
          </button>
        </div>
        {error ? <p className="mt-4 text-sm text-ember">{error}</p> : null}
        {generationResult ? (
          <p className="mt-4 text-sm text-moss">
            Quiz ready: {generationResult.question_count} questions covering {generationResult.concept_coverage.join(", ")}.
          </p>
        ) : null}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <article className="rounded-[32px] border border-ink/10 bg-white/85 p-6 shadow-glow">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-2xl font-semibold text-ink">Extracted concepts</h3>
            <span className="rounded-full bg-sand px-3 py-1 text-xs font-medium text-ink/70">
              {lecture.ai_metadata.used_fallback ? "Fallback AI" : "OpenAI"}
            </span>
          </div>
          <div className="space-y-4">
            {lecture.concepts.map((concept) => (
              <div className="rounded-2xl border border-ink/8 bg-mist/45 p-4" key={concept.id}>
                <div className="flex flex-wrap items-center gap-3">
                  <h4 className="font-semibold text-ink">{concept.name}</h4>
                  {concept.is_inferred ? (
                    <span className="rounded-full bg-clay/15 px-3 py-1 text-xs font-semibold text-clay">
                      inferred prerequisite
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm leading-7 text-ink/70">{concept.description}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[32px] border border-ink/10 bg-ink p-6 text-sand shadow-glow">
          <p className="text-xs uppercase tracking-[0.24em] text-sand/65">Study takeaways</p>
          <ul className="mt-4 space-y-3 text-sm leading-7 text-sand/80">
            {lecture.summary_block.key_takeaways.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-sand/55">Quiz status</p>
            <p className="mt-2 text-2xl font-semibold">{lecture.question_count} questions ready</p>
            <p className="mt-2 text-sm text-sand/75">
              The browser quiz and the future Unity client both use the same backend session APIs.
            </p>
          </div>
        </article>
      </section>
    </div>
  );
}
