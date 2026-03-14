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
    return <div className="rounded-[32px] bg-white/70 p-8 shadow-glow">Loading quiz...</div>;
  }

  if (finishResult || session.status === "completed") {
    const summary = finishResult;
    return (
      <div className="space-y-8">
        <section className="rounded-[36px] border border-moss/20 bg-moss p-8 text-white shadow-glow">
          <p className="text-xs uppercase tracking-[0.2em] text-white/70">Session finished</p>
          <h2 className="mt-3 text-4xl font-semibold">{session.lecture_title}</h2>
          <p className="mt-4 text-sm leading-7 text-white/80">
            Score: {summary ? Math.round(summary.score * 100) : Math.round((session.correct_answers / session.total_questions) * 100)}%
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-moss" href="/dashboard">
              View analytics
            </Link>
            <Link className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-white" href="/recommendations">
              View recommendations
            </Link>
          </div>
        </section>

        {summary ? (
          <section className="grid gap-6 lg:grid-cols-[1fr,1fr]">
            <div className="rounded-[32px] border border-ink/10 bg-white/80 p-6 shadow-glow">
              <h3 className="text-2xl font-semibold text-ink">Weak concepts</h3>
              <div className="mt-4 flex flex-wrap gap-3">
                {summary.weak_concepts.map((concept) => (
                  <span className="rounded-full bg-ember/10 px-4 py-2 text-sm font-medium text-ember" key={concept}>
                    {concept}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-[32px] border border-ink/10 bg-white/80 p-6 shadow-glow">
              <h3 className="text-2xl font-semibold text-ink">Recommendation preview</h3>
              <div className="mt-4 space-y-3">
                {summary.recommendations.map((recommendation) => (
                  <div className="rounded-2xl bg-mist/45 p-4" key={recommendation.recommendation_id}>
                    <p className="text-sm font-semibold text-ink">
                      {recommendation.rank}. {recommendation.title}
                    </p>
                    <p className="mt-2 text-sm leading-7 text-ink/70">{recommendation.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : null}
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="space-y-6">
        <div className="rounded-[32px] bg-white/80 p-8 shadow-glow">All questions answered. Finish the session to refresh recommendations.</div>
        <button
          className="rounded-full bg-clay px-5 py-3 text-sm font-semibold text-white"
          onClick={handleFinish}
          type="button"
        >
          Finish session
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[36px] border border-ink/10 bg-white/80 p-8 shadow-glow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-clay">Quiz session</p>
            <h2 className="mt-3 text-4xl font-semibold text-ink">{session.lecture_title}</h2>
          </div>
          <span className="rounded-full bg-sand px-4 py-2 text-sm font-semibold text-ink/70">
            Question {currentQuestion.sequence} / {questions.length}
          </span>
        </div>
      </section>

      <section className="rounded-[32px] border border-ink/10 bg-white/85 p-7 shadow-glow">
        <p className="text-xs uppercase tracking-[0.18em] text-moss">{currentQuestion.concept_name}</p>
        <h3 className="mt-3 text-2xl font-semibold text-ink">{currentQuestion.prompt}</h3>
        <div className="mt-6 space-y-3">
          {currentQuestion.choices.map((choice) => {
            const active = selectedChoiceId === choice.choice_id;
            return (
              <button
                className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                  active ? "border-clay bg-clay/10" : "border-ink/10 bg-mist/40 hover:bg-white"
                }`}
                key={choice.choice_id}
                onClick={() => setSelectedChoiceId(choice.choice_id)}
                type="button"
              >
                <span className="mr-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-ink text-sm font-semibold text-sand">
                  {choice.choice_id}
                </span>
                <span className="text-sm leading-7 text-ink/75">{choice.text}</span>
              </button>
            );
          })}
        </div>

        {!answerResult ? (
          <button
            className="mt-6 rounded-full bg-clay px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
            disabled={!selectedChoiceId || working}
            onClick={handleSubmitAnswer}
            type="button"
          >
            Submit answer
          </button>
        ) : (
          <div className="mt-6 rounded-[28px] border border-ink/10 bg-mist/45 p-6">
            <p className={`text-sm font-semibold ${answerResult.is_correct ? "text-moss" : "text-ember"}`}>
              {answerResult.is_correct ? "Correct answer" : "Needs review"}
            </p>
            <p className="mt-3 text-sm leading-7 text-ink/75">{answerResult.explanation}</p>
            <p className="mt-3 text-sm text-ink/65">
              Mastery for {answerResult.mastery.concept_name}: {(answerResult.mastery.mastery_score * 100).toFixed(0)}%
            </p>
            {currentIndex < questions.length - 1 ? (
              <button
                className="mt-5 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-sand"
                onClick={handleNext}
                type="button"
              >
                Next question
              </button>
            ) : (
              <button
                className="mt-5 rounded-full bg-ink px-5 py-3 text-sm font-semibold text-sand"
                onClick={handleFinish}
                type="button"
              >
                Finish session
              </button>
            )}
          </div>
        )}
        {error ? <p className="mt-4 text-sm text-ember">{error}</p> : null}
      </section>
    </div>
  );
}
