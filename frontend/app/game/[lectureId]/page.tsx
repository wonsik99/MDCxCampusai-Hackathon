"use client";

import { useParams, useRouter } from "next/navigation";

export default function GamePage() {
  const params = useParams<{ lectureId: string }>();
  const router = useRouter();

  return (
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Game mode</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(2.2rem,4.2vw,4.3rem)] font-medium leading-[0.94] tracking-[-0.07em] text-[var(--text-strong)]">
          Interactive learning game
        </h1>
        <p className="plain-note mt-4 max-w-3xl">
          This is the game-mode entry for the selected lecture. The full
          interactive experience is currently in progress.
        </p>
      </section>

      <section className="plain-section">
        <p className="eyebrow">Current lecture</p>
        <p className="mt-4 text-lg text-[var(--text-strong)]">
          Lecture ID: {params.lectureId}
        </p>
      </section>

      <section className="plain-section">
        <p className="eyebrow">Status</p>
        <div className="mt-4 space-y-3">
          <p className="plain-note">
            Game mechanics and interaction flow are being implemented.
          </p>
          <p className="plain-note">
            Quiz mode is available now. Game mode will use the same lecture
            concepts and generated learning content.
          </p>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="btn-secondary"
            onClick={() => router.back()}
            type="button"
          >
            Go back
          </button>
        </div>
      </section>
    </div>
  );
}
