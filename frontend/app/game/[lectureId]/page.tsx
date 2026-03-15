"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { API_BASE_URL, getLecture, getQuizSession, startQuizSession } from "@/lib/api";
import { LectureDetail, QuizSessionRead } from "@/lib/types";

export default function GamePage() {
  const params = useParams<{ lectureId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { selectedUser } = useUserContext();
  const [lecture, setLecture] = useState<LectureDetail | null>(null);
  const [session, setSession] = useState<QuizSessionRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [frameLoaded, setFrameLoaded] = useState(false);
  const [frameWarning, setFrameWarning] = useState<string | null>(null);
  const autoStartRef = useRef<string | null>(null);
  const incomingSessionId = searchParams.get("sessionId");

  useEffect(() => {
    if (!selectedUser) {
      setLoading(false);
      return;
    }
    const currentUser = selectedUser;

    async function loadGameContext() {
      setLoading(true);
      try {
        const lectureData = await getLecture(currentUser.id, params.lectureId);
        setLecture(lectureData);

        if (!lectureData.quiz_generated) {
          setError("Generate learning content before opening game mode.");
          setSession(null);
          return;
        }

        let activeSessionId = incomingSessionId;
        if (!activeSessionId) {
          const launchKey = `${currentUser.id}:${lectureData.id}`;
          if (autoStartRef.current === launchKey) {
            return;
          }
          autoStartRef.current = launchKey;
          setLaunching(true);
          const startedSession = await startQuizSession(currentUser.id, lectureData.id);
          activeSessionId = startedSession.session_id;
          router.replace(`/game/${lectureData.id}?sessionId=${startedSession.session_id}`);
        }

        if (!activeSessionId) {
          throw new Error("Unable to create a shared practice session.");
        }

        const sessionData = await getQuizSession(currentUser.id, activeSessionId);
        setSession(sessionData);
        setError(null);
      } catch (caught) {
        setError(
          caught instanceof Error ? caught.message : "Unable to open game mode.",
        );
      } finally {
        setLaunching(false);
        setLoading(false);
      }
    }

    void loadGameContext();
  }, [incomingSessionId, params.lectureId, router, selectedUser]);

  useEffect(() => {
    if (!selectedUser || !incomingSessionId) {
      return;
    }

    const interval = window.setInterval(() => {
      void getQuizSession(selectedUser.id, incomingSessionId)
        .then((sessionData) => {
          setSession(sessionData);
          if (sessionData.status === "completed") {
            setFrameWarning(null);
          }
        })
        .catch(() => {
          // Ignore background polling failures and keep the current view stable.
        });
    }, 5000);

    return () => window.clearInterval(interval);
  }, [incomingSessionId, selectedUser]);

  useEffect(() => {
    if (!session) {
      return;
    }
    setFrameLoaded(false);
    setFrameWarning(null);
    const timeout = window.setTimeout(() => {
      setFrameWarning(
        "Unity is taking longer than expected to load. You can keep waiting or switch to the shared quiz view.",
      );
    }, 12000);

    return () => window.clearTimeout(timeout);
  }, [session?.session_id]);

  const unitySrc = useMemo(() => {
    if (!selectedUser || !session) {
      return null;
    }
    const params = new URLSearchParams({
      lectureId: session.lecture_id,
      sessionId: session.session_id,
      userId: selectedUser.id,
      apiBaseUrl: API_BASE_URL,
    });
    return `/unity/index.html?${params.toString()}`;
  }, [selectedUser, session]);

  if (!selectedUser) {
    return (
      <div className="space-y-6">
        <p className="eyebrow">Game mode</p>
        <p className="plain-note">Select a demo learner first.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="text-sm text-[var(--text-muted)]">Preparing game session...</div>;
  }

  if (error || !lecture) {
    return (
      <div className="space-y-8">
        <section>
          <p className="eyebrow">Game mode</p>
          <h1 className="mt-4 max-w-4xl text-[clamp(2rem,3.4vw,3.4rem)] font-medium leading-[0.96] tracking-[-0.06em] text-[var(--text-strong)]">
            Unable to launch practice
          </h1>
          <p className="plain-note mt-4 max-w-3xl">
            {error ?? "This lecture could not be opened in game mode."}
          </p>
        </section>

        <div className="flex flex-wrap gap-3">
          <Link className="btn-primary" href={`/lectures/${params.lectureId}`}>
            Return to lecture
          </Link>
          <button className="btn-secondary" onClick={() => router.back()} type="button">
            Go back
          </button>
        </div>
      </div>
    );
  }

  if (!lecture.quiz_generated) {
    return (
      <div className="space-y-8">
        <section>
          <p className="eyebrow">Game mode</p>
          <h1 className="mt-4 max-w-4xl text-[clamp(2rem,3.4vw,3.4rem)] font-medium leading-[0.96] tracking-[-0.06em] text-[var(--text-strong)]">
            Learning content required
          </h1>
          <p className="plain-note mt-4 max-w-3xl">
            Generate learning content first so quiz mode and game mode can use the same tracked adaptive session.
          </p>
        </section>

        <Link className="btn-primary" href={`/lectures/${lecture.id}`}>
          Open lecture workspace
        </Link>
      </div>
    );
  }

  if (!session) {
    return <div className="text-sm text-[var(--text-muted)]">Preparing shared practice session...</div>;
  }

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Game mode</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(2rem,3.4vw,3.4rem)] font-medium leading-[0.96] tracking-[-0.06em] text-[var(--text-strong)]">
          {lecture.title}
        </h1>
        <p className="plain-note mt-4 max-w-3xl">
          Game mode now launches with the same tracked practice session used by quiz mode, so progress and review stay in one flow.
        </p>

        <div className="plain-strip mt-8 grid gap-0 md:grid-cols-3">
          <div className="py-4 md:py-5 md:pr-6">
            <p className="eyebrow">Mode</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
              Unity WebGL
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:px-6 md:py-5">
            <p className="eyebrow">Session</p>
            <p className="mt-2 text-sm font-medium text-[var(--text-strong)]">
              {session?.session_id ?? "Preparing..."}
            </p>
          </div>
          <div className="py-4 md:border-l md:border-white/10 md:pl-6 md:py-5">
            <p className="eyebrow">Status</p>
            <p className="mt-2 text-lg font-medium tracking-[-0.04em] text-[var(--text-strong)]">
              {session?.status === "completed" ? "Completed" : launching ? "Launching" : "In progress"}
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-8">
        <div className="plain-section xl:pt-0 xl:border-t-0">
          {!frameLoaded ? (
            <div className="plain-strip mb-6 py-3">
              <p className="text-sm text-[var(--text-muted)]">
                {frameWarning ?? "Loading Unity WebGL build..."}
              </p>
            </div>
          ) : null}

          {unitySrc ? (
            <iframe
              allowFullScreen
              className="mx-auto block aspect-[8/5] w-full max-w-[960px] rounded-[28px] border border-white/10 bg-black shadow-[0_20px_80px_rgba(0,0,0,0.25)]"
              onError={() =>
                setFrameWarning(
                  "Unity failed to load. Check that the WebGL build files are present in frontend/public/unity.",
                )
              }
              onLoad={() => {
                setFrameLoaded(true);
                setFrameWarning(null);
              }}
              src={unitySrc}
              title="StruggleSense Unity game"
            />
          ) : (
            <div className="plain-note">Preparing Unity launch context...</div>
          )}
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <section className="plain-section xl:pt-0 xl:border-t-0">
            <p className="eyebrow">Shared adaptive session</p>
            <div className="mt-4 space-y-3 text-sm text-[var(--text-muted)]">
              <p>Both quiz mode and game mode start from the same backend session rules.</p>
              <p>When the practice session is complete, review results from the shared analytics flow.</p>
            </div>
          </section>

          <section className="plain-section">
            <p className="eyebrow">Next step</p>
            <div className="mt-4 flex flex-col gap-3">
              <Link
                className="btn-primary"
                href={`/quiz/${session.session_id}`}
              >
                {session?.status === "completed" ? "Open shared results" : "Open shared session view"}
              </Link>
              <Link className="btn-secondary" href={`/lectures/${lecture.id}`}>
                Back to lecture
              </Link>
            </div>
          </section>

          <section className="plain-section">
            <p className="eyebrow">Tracking</p>
            <div className="mt-4 space-y-3 text-sm text-[var(--text-muted)]">
              <p>Answered: {session?.answered_questions ?? 0} / {session?.total_questions ?? 0}</p>
              <p>Correct: {session?.correct_answers ?? 0}</p>
              <p>Status refreshes automatically while the game is open.</p>
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
