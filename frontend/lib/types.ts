export type AIUsageMetadata = {
  provider: string;
  used_fallback: boolean;
};

export type DemoUser = {
  id: string;
  name: string;
  email: string;
};

export type Concept = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  prerequisite_concept_id: string | null;
  is_inferred: boolean;
  display_order: number;
};

export type LectureSummaryBlock = {
  summary: string;
  key_takeaways: string[];
};

export type LectureListItem = {
  id: string;
  title: string;
  source_type: "pdf" | "text";
  summary: string | null;
  concept_count: number;
  question_count: number;
  created_at: string;
};

export type LectureDetail = {
  id: string;
  title: string;
  source_type: "pdf" | "text";
  original_filename: string | null;
  summary_block: LectureSummaryBlock;
  concepts: Concept[];
  question_count: number;
  quiz_generated: boolean;
  ai_metadata: AIUsageMetadata;
  created_at: string;
};

export type LectureUploadResponse = {
  lecture: LectureDetail;
  source_type: "pdf" | "text";
  cleaned_text_length: number;
};

export type QuizGenerationResponse = {
  lecture_id: string;
  question_count: number;
  concept_coverage: string[];
  generated: boolean;
  ai_metadata: AIUsageMetadata;
};

export type QuizSessionStartResponse = {
  session_id: string;
  lecture_id: string;
  lecture_title: string;
  lecture_summary: string;
  concept_ids: string[];
  session_status: "in_progress" | "completed";
  total_questions: number;
};

export type Choice = {
  choice_id: string;
  text: string;
};

export type QuizQuestion = {
  question_id: string;
  prompt: string;
  concept_id: string;
  concept_name: string;
  choices: Choice[];
  sequence: number;
};

export type QuizSessionQuestionsResponse = {
  session_id: string;
  questions: QuizQuestion[];
};

export type QuizSessionRead = {
  session_id: string;
  lecture_id: string;
  lecture_title: string;
  status: "in_progress" | "completed";
  total_questions: number;
  answered_questions: number;
  correct_answers: number;
  started_at: string;
  finished_at: string | null;
};

export type ConceptMasterySnapshot = {
  concept_id: string;
  concept_name: string;
  mastery_score: number;
  correct_count: number;
  wrong_count: number;
};

export type SubmitAnswerResponse = {
  session_id: string;
  question_id: string;
  is_correct: boolean;
  correct_choice_id: string;
  correct_choice_text: string;
  explanation: string;
  mastery: ConceptMasterySnapshot;
  is_weak_concept: boolean;
};

export type ConceptPerformance = {
  concept_id: string;
  concept_name: string;
  correct: number;
  wrong: number;
  mastery_score: number;
};

export type Recommendation = {
  recommendation_id: string;
  rank: number;
  lecture_id: string | null;
  lecture_title: string | null;
  concept_id: string | null;
  concept_name: string | null;
  reason_code: string;
  title: string;
  message: string;
};

export type FinishSessionResponse = {
  session_id: string;
  score: number;
  correct_answers: number;
  total_questions: number;
  concept_performance: ConceptPerformance[];
  weak_concepts: string[];
  recommendations: Recommendation[];
};

export type ConceptMasteryRead = {
  concept_id: string;
  lecture_id: string;
  lecture_title: string;
  concept_name: string;
  concept_slug: string;
  mastery_score: number;
  correct_count: number;
  wrong_count: number;
  prerequisite_concept_id: string | null;
  is_weak: boolean;
};

export type RecommendationsResponse = {
  user_id: string;
  recommendations: Recommendation[];
};
