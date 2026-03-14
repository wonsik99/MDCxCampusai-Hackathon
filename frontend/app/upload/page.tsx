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
    <div className="space-y-10">
      <section>
        <p className="eyebrow">Upload</p>
        <h1 className="mt-4 max-w-4xl text-[clamp(2.2rem,4.2vw,4.3rem)] font-medium leading-[0.94] tracking-[-0.07em] text-[var(--text-strong)]">
          Add a lecture.
        </h1>
      </section>

      <form className="grid gap-10 xl:grid-cols-[minmax(0,1fr),320px]" onSubmit={onSubmit}>
        <section className="space-y-8">
          <label className="block">
            <span className="eyebrow">Title</span>
            <input
              className="field mt-3"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Linear Algebra Lecture 4"
              value={title}
            />
          </label>

          <label className="block">
            <span className="eyebrow">Text</span>
            <textarea
              className="field-area mt-3"
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste lecture notes here."
              value={rawText}
            />
          </label>

          <div className="plain-section">
            <p className="eyebrow">PDF</p>
            <label className="mt-4 block rounded-[16px] border border-dashed border-white/[0.18] bg-white/[0.05] px-4 py-6 text-sm text-[var(--text-muted)] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur-xl">
              <span className="block font-medium text-[var(--text-strong)]">
                {file ? file.name : "Choose a PDF"}
              </span>
              <input
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                type="file"
              />
            </label>
          </div>
        </section>

        <aside className="space-y-8">
          <section className="plain-section xl:pt-0 xl:border-t-0">
            <p className="eyebrow">Rules</p>
            <div className="mt-4 space-y-2 text-sm text-[var(--text-muted)]">
              <p>Use text or PDF.</p>
              <p>Learner: {selectedUser?.name ?? "Not selected"}</p>
            </div>
          </section>

          <section className="plain-section">
            <button className="btn-primary w-full" disabled={submitting} type="submit">
              {submitting ? "Analyzing..." : "Upload"}
            </button>
            {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}
          </section>

          <section className="plain-section">
            <p className="eyebrow">Result</p>
            {result ? (
              <>
                <h2 className="section-title mt-3">{result.lecture.title}</h2>
                <Link className="editorial-link mt-6" href={`/lectures/${result.lecture.id}`}>
                  Open lecture
                </Link>
              </>
            ) : (
              <p className="plain-note mt-4">Nothing uploaded yet.</p>
            )}
          </section>
        </aside>
      </form>
    </div>
  );
}
