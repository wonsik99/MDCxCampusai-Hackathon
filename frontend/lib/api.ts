import {
  ConceptMasteryRead,
  DemoUser,
  FinishSessionResponse,
  LectureDetail,
  LectureListItem,
  LectureUploadResponse,
  QuizGenerationResponse,
  QuizSessionQuestionsResponse,
  QuizSessionRead,
  QuizSessionStartResponse,
  RecommendationsResponse,
  SubmitAnswerResponse
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type JsonBody = Record<string, unknown> | undefined;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly details?: unknown
  ) {
    super(message);
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  userId?: string
): Promise<T> {
  const headers = new Headers(options.headers);
  if (userId) {
    headers.set("X-User-Id", userId);
  }
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store"
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(data.message ?? "API request failed.", response.status, data.details);
  }
  return data as T;
}

function toJsonBody(body?: JsonBody) {
  return body ? JSON.stringify(body) : undefined;
}

export function listDemoUsers() {
  return apiFetch<DemoUser[]>("/demo-users");
}

export function listLectures(userId: string) {
  return apiFetch<LectureListItem[]>("/lectures", {}, userId);
}

export function getLecture(userId: string, lectureId: string) {
  return apiFetch<LectureDetail>(`/lectures/${lectureId}`, {}, userId);
}

export function uploadLecture(
  userId: string,
  payload: { title?: string; rawText?: string; file?: File | null }
) {
  const formData = new FormData();
  if (payload.title) {
    formData.append("title", payload.title);
  }
  if (payload.rawText) {
    formData.append("raw_text", payload.rawText);
  }
  if (payload.file) {
    formData.append("file", payload.file);
  }
  return apiFetch<LectureUploadResponse>("/lectures/upload", { method: "POST", body: formData }, userId);
}

export function generateQuiz(userId: string, lectureId: string, forceRegenerate = false) {
  return apiFetch<QuizGenerationResponse>(
    `/lectures/${lectureId}/generate-quiz`,
    { method: "POST", body: toJsonBody({ force_regenerate: forceRegenerate, questions_per_concept: 2 }) },
    userId
  );
}

export function startQuizSession(userId: string, lectureId: string) {
  return apiFetch<QuizSessionStartResponse>(
    "/quiz-sessions/start",
    { method: "POST", body: toJsonBody({ lecture_id: lectureId }) },
    userId
  );
}

export function getQuizSession(userId: string, sessionId: string) {
  return apiFetch<QuizSessionRead>(`/quiz-sessions/${sessionId}`, {}, userId);
}

export function getQuizQuestions(userId: string, sessionId: string) {
  return apiFetch<QuizSessionQuestionsResponse>(`/quiz-sessions/${sessionId}/questions`, {}, userId);
}

export function submitAnswer(
  userId: string,
  sessionId: string,
  questionId: string,
  selectedChoiceId: string,
  responseTimeMs: number
) {
  return apiFetch<SubmitAnswerResponse>(
    `/quiz-sessions/${sessionId}/submit-answer`,
    {
      method: "POST",
      body: toJsonBody({
        question_id: questionId,
        selected_choice_id: selectedChoiceId,
        response_time_ms: responseTimeMs
      })
    },
    userId
  );
}

export function finishQuizSession(userId: string, sessionId: string) {
  return apiFetch<FinishSessionResponse>(
    `/quiz-sessions/${sessionId}/finish`,
    { method: "POST" },
    userId
  );
}

export function getConceptMastery(userId: string) {
  return apiFetch<ConceptMasteryRead[]>(`/users/${userId}/concept-mastery`);
}

export function getRecommendations(userId: string) {
  return apiFetch<RecommendationsResponse>(`/users/${userId}/recommendations`);
}
