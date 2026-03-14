import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecommendationList } from "@/components/recommendation-list";

describe("RecommendationList", () => {
  it("renders ordered recommendations", () => {
    render(
      <RecommendationList
        recommendations={[
          {
            recommendation_id: "r1",
            rank: 1,
            lecture_id: "l1",
            lecture_title: "Linear Algebra",
            concept_id: "c1",
            concept_name: "Determinant",
            reason_code: "prerequisite_gap",
            title: "Rebuild determinant",
            message: "Review determinants before retrying eigenvalue questions."
          }
        ]}
      />
    );

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("Rebuild determinant")).toBeInTheDocument();
    expect(screen.getByText("prerequisite gap")).toBeInTheDocument();
  });
});
