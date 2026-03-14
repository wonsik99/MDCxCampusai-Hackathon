"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useUserContext } from "@/components/user-context";
import { uploadLecture } from "@/lib/api";
import { LectureUploadResponse } from "@/lib/types";

export default function UploadPage() {
  const { selectedUser } = useUserContext();
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<LectureUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedUser) {
      setError("Select a demo student first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await uploadLecture(selectedUser.id, { title, rawText, file });
      setResult(response);
      setRawText("");
      setFile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[36px] border border-ink/10 bg-white/80 p-8 shadow-glow">
        <p className="text-xs uppercase tracking-[0.22em] text-moss">Lecture ingestion</p>
        <h2 className="mt-3 text-4xl font-semibold text-ink" style={{ fontFamily: "var(--font-heading)" }}>
          Upload source material for concept extraction
        </h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-ink/70">
          Provide either a PDF or raw lecture text. The backend extracts clean text, summarizes it, identifies concepts, and stores metadata before quiz generation starts.
        </p>
      </section>

      <form className="grid gap-6 lg:grid-cols-[1.3fr,0.9fr]" onSubmit={onSubmit}>
        <div className="rounded-[32px] border border-ink/10 bg-white/85 p-6 shadow-glow">
          <label className="block text-sm font-medium text-ink">
            Lecture title
            <input
              className="mt-2 w-full rounded-2xl border border-ink/10 bg-mist/45 px-4 py-3 outline-none"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Linear Algebra Lecture 4"
              value={title}
            />
          </label>

          <label className="mt-5 block text-sm font-medium text-ink">
            Raw lecture text
            <textarea
              className="mt-2 min-h-[260px] w-full rounded-3xl border border-ink/10 bg-mist/45 px-4 py-4 outline-none"
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste lecture notes here, or leave blank and upload a PDF."
              value={rawText}
            />
          </label>
        </div>

        <div className="space-y-6">
          <section className="rounded-[32px] border border-ink/10 bg-white/80 p-6 shadow-glow">
            <label className="block text-sm font-medium text-ink">
              PDF upload
              <input
                accept=".pdf,application/pdf"
                className="mt-3 block w-full text-sm text-ink"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                type="file"
              />
            </label>
            <p className="mt-3 text-sm text-ink/65">
              Use one source at a time. If both raw text and a file are provided, the backend rejects the request.
            </p>
            <button
              className="mt-6 w-full rounded-full bg-clay px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
              disabled={submitting}
              type="submit"
            >
              {submitting ? "Analyzing lecture..." : "Upload and analyze"}
            </button>
            {error ? <p className="mt-3 text-sm text-ember">{error}</p> : null}
          </section>

          {result ? (
            <section className="rounded-[32px] border border-moss/20 bg-moss p-6 text-white shadow-glow">
              <p className="text-xs uppercase tracking-[0.22em] text-white/70">Upload complete</p>
              <h3 className="mt-3 text-2xl font-semibold">{result.lecture.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/80">{result.lecture.summary_block.summary}</p>
              <Link className="mt-5 inline-flex rounded-full bg-white px-4 py-2 text-sm font-semibold text-moss" href={`/lectures/${result.lecture.id}`}>
                Open lecture detail
              </Link>
            </section>
          ) : null}
        </div>
      </form>
    </div>
  );
}
