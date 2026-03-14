"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { finishQuizSession, getQuizQuestions, getQuizSession, submitAnswer } from "@/lib/api";
import {
  FinishSessionResponse,
  QuizQuestion,
  QuizSessionRead,
  SubmitAnswerResponse
} from "@/lib/types";

export default function QuizPage() {
  const params = useParams<{ sessionId: string }>();
  const { selectedUser } = useUserContext();
  const [session, setSession] = useState<QuizSessionRead | null>(null);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const [answerResult, setAnswerResult] = useState<SubmitAnswerResponse | null>(null);
  const [finishResult, setFinishResult] = useState<FinishSessionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const startedAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }
    startedAtRef.current = Date.now();
    void Promise.all([
      getQuizSession(selectedUser.id, params.sessionId),
      getQuizQuestions(selectedUser.id, params.sessionId)
    ])
      .then(([sessionData, questionData]) => {
        setSession(sessionData);
        setQuestions(questionData.questions);
        setCurrentIndex(sessionData.answered_questions);
        setError(null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load quiz session."));
  }, [params.sessionId, selectedUser]);

  const currentQuestion = useMemo(() => questions[currentIndex] ?? null, [questions, currentIndex]);

  async function handleSubmitAnswer() {
    if (!selectedUser || !currentQuestion || !selectedChoiceId || !startedAtRef.current) return;
    setWorking(true);
    try {
      const result = await submitAnswer(
        selectedUser.id,
        params.sessionId,
        currentQuestion.question_id,
        selectedChoiceId,
        Date.now() - startedAtRef.current
      );
      setAnswerResult(result);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to submit answer.");
    } finally {
      setWorking(false);
    }
  }

  function handleNext() {
    setCurrentIndex((index) => index + 1);
    setSelectedChoiceId(null);
    setAnswerResult(null);
    startedAtRef.current = Date.now();
  }

  async function handleFinish() {
    if (!selectedUser) return;
    setWorking(true);
    try {
      const result = await finishQuizSession(selectedUser.id, params.sessionId);
      setFinishResult(result);
      const refreshed = await getQuizSession(selectedUser.id, params.sessionId);
      setSession(refreshed);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to finish session.");
    } finally {
      setWorking(false);
    }
  }

  if (!session) {
    return <div className="text-sm text-[var(--text-muted)]">Loading quiz...</div>;
  }

  if (finishResult || session.status === "completed") {
    const summary = finishResult;
    return (
      <div className="space-y-10">
        <section>
          <p className="eyebrow">Session finished</p>
          <h1 className="mt-4 max-w-4xl text-[clamp(2.2rem,4.2vw,4.3rem)] font-medium leading-[0.94] tracking-[-0.07em] text-[var(--text-strong)]">
            {session.lecture_title}
          </h1>
          <div className="plain-strip mt-8 py-4">
            <p className="text-sm text-[var(--text-muted)]">
              Score {summary
                ? Math.round(summary.score * 100)
                : Math.round((session.correct_answers / session.total_questions) * 100)}
              %
            </p>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="btn-primary" href="/dashboard">
              Analytics
            </Link>
            <Link className="btn-secondary" href="/recommendations">
              Recommendations
            </Link>
          </div>
        </section>

        {summary ? (
          <section className="grid gap-10 lg:grid-cols-[0.9fr,1.1fr]">
            <section className="plain-section lg:pt-0 lg:border-t-0">
              <p className="eyebrow">Weak concepts</p>
              <div className="mt-6 flex flex-wrap gap-3">
                {summary.weak_concepts.map((concept) => (
                  <span className="badge-primary" key={concept}>
                    {concept}
                  </span>
                ))}
              </div>
            </section>

            <section className="plain-section lg:pt-0 lg:border-t-0">
              <p className="eyebrow">Recommendations</p>
              <div className="mt-6 divide-y divide-white/10">
                {summary.recommendations.map((recommendation) => (
                  <div className="py-4 first:pt-0 last:pb-0" key={recommendation.recommendation_id}>
                    <p className="text-sm font-semibold text-[var(--text-strong)]">
                      {recommendation.rank}. {recommendation.title}
                    </p>
                    <p className="plain-note mt-2">{recommendation.message}</p>
                  </div>
                ))}
              </div>
            </section>
          </section>
        ) : null}
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="space-y-6">
        <div className="text-sm leading-7 text-[var(--text-muted)]">All questions answered.</div>
        <button className="btn-primary" onClick={handleFinish} type="button">
          Finish session
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Quiz</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(2.2rem,4.2vw,4.3rem)] font-medium leading-[0.94] tracking-[-0.07em] text-[var(--text-strong)]">
          {session.lecture_title}
        </h1>
        <div className="plain-strip mt-8 grid gap-0 md:grid-cols-3">
          <div className="py-4 md:py-5 md:pr-6">
            <p className="eyebrow">Question</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
              {currentQuestion.sequence} / {questions.length}
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:px-6 md:py-5">
            <p className="eyebrow">Answered</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">{currentIndex}</p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:pl-6 md:py-5">
            <p className="eyebrow">Correct</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">{session.correct_answers}</p>
          </div>
        </div>
      </section>

      <section className="plain-section">
        <p className="eyebrow">{currentQuestion.concept_name}</p>
        <h2 className="section-title mt-4 text-[1.9rem]">{currentQuestion.prompt}</h2>

        <div className="mt-8 space-y-3">
          {currentQuestion.choices.map((choice) => {
            const active = selectedChoiceId === choice.choice_id;
            const isAnswered = Boolean(answerResult);
            const isCorrectChoice = answerResult?.correct_choice_id === choice.choice_id;
            const isWrongSelected = isAnswered && active && !isCorrectChoice;
            return (
              <button
                className={`w-full border px-4 py-4 text-left transition ${
                  isCorrectChoice
                    ? "border-emerald-300/70 bg-emerald-500/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                    : isWrongSelected
                      ? "border-red-300/70 bg-red-500/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                      : active
                    ? "border-white/[0.24] bg-white/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-xl"
                    : "border-white/10 bg-white/[0.04] hover:border-white/[0.18] hover:bg-white/[0.06]"
                }`}
                disabled={isAnswered}
                key={choice.choice_id}
                onClick={() => {
                  if (!isAnswered) {
                    setSelectedChoiceId(choice.choice_id);
                  }
                }}
                type="button"
              >
                <div className="flex items-start gap-4">
                  <span
                    className={`flex h-8 w-8 items-center justify-center border text-sm font-semibold ${
                      isCorrectChoice
                        ? "border-emerald-300/70 bg-emerald-400/25 text-[var(--text-strong)]"
                        : isWrongSelected
                          ? "border-red-300/70 bg-red-400/20 text-[var(--text-strong)]"
                          : active
                        ? "border-white/[0.24] bg-white/[0.16] text-[var(--text-strong)]"
                        : "border-white/10 bg-white/8 text-[var(--text-strong)]"
                    }`}
                  >
                    {choice.choice_id}
                  </span>
                  <div className="flex-1">
                    <span className="text-sm leading-7 text-[var(--text-strong)]">{choice.text}</span>
                    {isCorrectChoice ? (
                      <p className="mt-1 text-xs uppercase tracking-[0.1em] text-emerald-200">Correct answer</p>
                    ) : null}
                    {isWrongSelected ? (
                      <p className="mt-1 text-xs uppercase tracking-[0.1em] text-red-200">Your choice</p>
                    ) : null}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {!answerResult ? (
          <button
            className="btn-primary mt-8"
            disabled={!selectedChoiceId || working}
            onClick={handleSubmitAnswer}
            type="button"
          >
            Submit answer
          </button>
        ) : (
          <div className="plain-section mt-8">
            <p className="text-sm font-semibold text-[var(--text-strong)]">
              {answerResult.is_correct ? "Correct answer" : "Needs review"}
            </p>
            <p className="plain-note mt-3">{answerResult.explanation}</p>
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              Mastery for {answerResult.mastery.concept_name}: {(answerResult.mastery.mastery_score * 100).toFixed(0)}%
            </p>
            {currentIndex < questions.length - 1 ? (
              <button className="btn-secondary mt-6" onClick={handleNext} type="button">
                Next question
              </button>
            ) : (
              <button className="btn-secondary mt-6" onClick={handleFinish} type="button">
                Finish session
              </button>
            )}
          </div>
        )}

        {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}
      </section>
    </div>
  );
}
