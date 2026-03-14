"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { generateQuiz, getLecture, startQuizSession } from "@/lib/api";
import { LectureDetail, QuizGenerationResponse } from "@/lib/types";

export default function LectureDetailPage() {
  const params = useParams<{ lectureId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { selectedUser } = useUserContext();
  const [lecture, setLecture] = useState<LectureDetail | null>(null);
  const [generationResult, setGenerationResult] =
    useState<QuizGenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [workingLabel, setWorkingLabel] = useState("");
  const autoGenerationTriggeredRef = useRef(false);

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
      .catch((caught) =>
        setError(
          caught instanceof Error ? caught.message : "Failed to load lecture.",
        ),
      )
      .finally(() => setLoading(false));
  }, [params.lectureId, selectedUser]);

  async function handleGenerateQuiz() {
    if (!selectedUser || !lecture) return;
    setWorking(true);
    setWorkingLabel("Generating quiz...");
    try {
      const response = await generateQuiz(selectedUser.id, lecture.id);
      setGenerationResult(response);
      const refreshed = await getLecture(selectedUser.id, lecture.id);
      setLecture(refreshed);
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Quiz generation failed.",
      );
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    if (
      !selectedUser ||
      !lecture ||
      working ||
      autoGenerationTriggeredRef.current
    ) {
      return;
    }
    if (searchParams.get("autogen") !== "1") {
      return;
    }
    if (lecture.quiz_generated) {
      autoGenerationTriggeredRef.current = true;
      router.replace(`/lectures/${lecture.id}`);
      return;
    }
    autoGenerationTriggeredRef.current = true;
    void handleGenerateQuiz().finally(() => {
      router.replace(`/lectures/${lecture.id}`);
    });
  }, [lecture, router, searchParams, selectedUser, working]);

  async function handleStartQuiz() {
    if (!selectedUser || !lecture) return;
    setWorking(true);
    setWorkingLabel("Starting session...");
    try {
      const session = await startQuizSession(selectedUser.id, lecture.id);
      router.push(`/quiz/${session.session_id}`);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to start quiz.",
      );
      setWorking(false);
    }
  }

  async function handleStartGame() {
    if (!selectedUser || !lecture) return;
    setWorking(true);
    setWorkingLabel("Opening game mode...");
    try {
      router.push(`/game/${lecture.id}`);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to start game.",
      );
      setWorking(false);
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-[var(--text-muted)]">Loading lecture...</div>
    );
  }

  if (!lecture) {
    return (
      <div className="text-sm text-[var(--text-muted)]">Lecture not found.</div>
    );
  }

  const workflowSteps = [
    { label: "Upload", done: true },
    { label: "Generate Flashcards", done: lecture.quiz_generated },
    { label: "Quiz or Game", done: false },
    { label: "Review recommendations", done: false },
  ];

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Lecture</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(1.8rem,3.2vw,3rem)] font-medium leading-[0.98] tracking-[-0.05em] text-[var(--text-strong)]">
          {lecture.title}
        </h1>
        <div className="mt-6 flex flex-wrap gap-3">
          <span className="badge">{lecture.source_type}</span>
        </div>

        <div className="plain-strip mt-8 grid gap-0 md:grid-cols-3">
          <div className="py-4 md:py-5 md:pr-6">
            <p className="eyebrow">Concepts</p>
            <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">
              {lecture.concepts.length}
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:px-6 md:py-5">
            <p className="eyebrow">Questions</p>
            <p className="mt-2 text-[2rem] font-medium tracking-[-0.08em] text-[var(--text-strong)]">
              {lecture.question_count}
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:pl-6 md:py-5">
            <p className="eyebrow">Provider</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
              {lecture.ai_metadata.used_fallback ? "Fallback" : "OpenAI"}
            </p>
          </div>
        </div>
      </section>

      <section className="plain-section">
        <p className="eyebrow">Workflow</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {workflowSteps.map((step, index) => {
            const isCurrent =
              index === 1
                ? !lecture.quiz_generated
                : index === 2
                  ? lecture.quiz_generated
                  : false;
            return (
              <div
                className={`list-row flex items-center gap-3 ${isCurrent ? "border-[var(--border-strong)]" : ""}`}
                key={step.label}
              >
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                    step.done
                      ? "bg-[var(--accent-warm)] text-black"
                      : isCurrent
                        ? "bg-white/20 text-[var(--text-strong)]"
                        : "bg-white/10 text-[var(--text-muted)]"
                  }`}
                >
                  {step.done ? "✓" : index + 1}
                </span>
                <span className="text-xs tracking-[0.07em] text-[var(--text-muted)] uppercase">
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="plain-section">
        <p className="eyebrow">Summary</p>
        <p className="plain-note mt-4 max-w-4xl">
          {lecture.summary_block.summary}
        </p>
      </section>

      <section className="plain-section">
        <div className="flex flex-wrap gap-3">
          <button
            className="btn-primary"
            disabled={working}
            onClick={handleGenerateQuiz}
            type="button"
          >
            {working && workingLabel === "Generating quiz..." ? (
              <span className="inline-flex items-center gap-2">
                <span className="loading-inline-spinner" />
                Generating...
              </span>
            ) : lecture.quiz_generated ? (
              "Regenerate content"
            ) : (
              "Generate learning content"
            )}
          </button>
        </div>

        {working ? <p className="loading-inline mt-3">{workingLabel}</p> : null}

        {!lecture.quiz_generated ? (
          <p className="plain-note mt-3">
            Generate learning content first, then choose quiz mode or game mode.
          </p>
        ) : null}

        {generationResult ? (
          <p className="plain-note mt-4">
            {generationResult.question_count} questions ready.
          </p>
        ) : null}

        {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}

        {lecture.quiz_generated ? (
          <div className="mt-10">
            <p className="eyebrow">Choose mode</p>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="rounded-[32px] border border-white/10 bg-white/[0.04] p-8 min-h-[420px] flex flex-col">
                <p className="eyebrow">Quiz mode</p>
                <h3 className="mt-4 text-[2.2rem] leading-[1.05] font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                  Fast diagnostic check
                </h3>
                <p className="plain-note mt-4 max-w-[34rem]">
                  Best for quickly measuring understanding, identifying weak
                  concepts, and getting immediate answer feedback.
                </p>
                <ul className="mt-6 space-y-3 text-base text-[var(--text-muted)]">
                  <li>• Multiple-choice questions</li>
                  <li>• Immediate correctness feedback</li>
                  <li>• Supports mastery tracking</li>
                </ul>
                <button
                  className="btn-primary mt-auto w-fit px-8 py-4 text-base"
                  disabled={working}
                  onClick={handleStartQuiz}
                  type="button"
                >
                  {working && workingLabel === "Starting session..." ? (
                    <span className="inline-flex items-center gap-2">
                      <span className="loading-inline-spinner" />
                      Starting...
                    </span>
                  ) : (
                    "Start quiz"
                  )}
                </button>
              </div>

              <div className="rounded-[32px] border border-white/10 bg-white/[0.04] p-8 min-h-[420px] flex flex-col">
                <p className="eyebrow">Game mode</p>
                <h3 className="mt-4 text-[2.2rem] leading-[1.05] font-medium tracking-[-0.06em] text-[var(--text-strong)]">
                  Interactive learning play
                </h3>
                <p className="plain-note mt-4 max-w-[34rem]">
                  Best for engagement, repeated practice, and turning study into
                  a more motivating experience.
                </p>
                <ul className="mt-6 space-y-3 text-base text-[var(--text-muted)]">
                  <li>• Same concepts, different experience</li>
                  <li>• More playful and immersive</li>
                  <li>• Good for reinforcement and retention</li>
                </ul>
                <button
                  className="btn-secondary mt-auto w-fit px-8 py-4 text-base"
                  disabled={working}
                  onClick={handleStartGame}
                  type="button"
                >
                  {working && workingLabel === "Opening game mode..." ? (
                    <span className="inline-flex items-center gap-2">
                      <span className="loading-inline-spinner" />
                      Opening...
                    </span>
                  ) : (
                    "Play game"
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </section>

      <section className="grid gap-10 xl:grid-cols-[minmax(0,1fr),320px]">
        <section className="plain-section xl:pt-0 xl:border-t-0">
          <p className="eyebrow">Concepts</p>
          <div className="mt-6 divide-y divide-white/10">
            {lecture.concepts.map((concept, index) => (
              <div
                className="grid gap-4 py-4 first:pt-0 last:pb-0 md:grid-cols-[40px,1fr]"
                key={concept.id}
              >
                <p className="text-[1.1rem] font-medium tracking-[-0.05em] text-[var(--text-strong)]">
                  {index + 1}
                </p>
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-[1.05rem] font-medium tracking-[-0.04em] text-[var(--text-strong)]">
                      {concept.name}
                    </h3>
                    {concept.is_inferred ? (
                      <span className="text-[0.72rem] uppercase tracking-[0.12em] text-[var(--text-muted)]">
                        Prerequisite
                      </span>
                    ) : null}
                  </div>
                  <p className="plain-note mt-2">{concept.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="plain-section xl:pt-0 xl:border-t-0">
          <p className="eyebrow">Takeaways</p>
          <div className="mt-6 divide-y divide-white/10">
            {lecture.summary_block.key_takeaways.map((item) => (
              <p
                className="py-3 text-sm leading-7 text-[var(--text-muted)] first:pt-0 last:pb-0"
                key={item}
              >
                {item}
              </p>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}
