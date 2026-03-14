import { describe, expect, it } from "vitest";

import { getWeakConcepts, groupMasteryByLecture } from "@/lib/analytics";
import { ConceptMasteryRead } from "@/lib/types";

const sample: ConceptMasteryRead[] = [
  {
    concept_id: "1",
    lecture_id: "a",
    lecture_title: "Lecture A",
    concept_name: "Determinant",
    concept_slug: "determinant",
    mastery_score: 0.45,
    correct_count: 1,
    wrong_count: 3,
    prerequisite_concept_id: null,
    is_weak: true
  },
  {
    concept_id: "2",
    lecture_id: "a",
    lecture_title: "Lecture A",
    concept_name: "Eigenvalues",
    concept_slug: "eigenvalues",
    mastery_score: 0.8,
    correct_count: 4,
    wrong_count: 1,
    prerequisite_concept_id: "1",
    is_weak: false
  }
];

describe("analytics helpers", () => {
  it("filters weak concepts", () => {
    expect(getWeakConcepts(sample)).toHaveLength(1);
  });

  it("groups rows by lecture title", () => {
    expect(Object.keys(groupMasteryByLecture(sample))).toEqual(["Lecture A"]);
  });
});
