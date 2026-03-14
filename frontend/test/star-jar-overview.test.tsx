import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StarJarOverview } from "@/components/star-jar-overview";

describe("StarJarOverview", () => {
  it("renders the current jar and archived history", () => {
    render(
      <StarJarOverview
        currentJar={{
          jar_id: "current",
          week_start_date: "2026-03-09",
          week_end_date: "2026-03-15",
          capacity_stars: 100,
          earned_stars: 42,
          fill_ratio: 0.42,
          study_time_ms: 420000,
          sessions_count: 3,
          average_accuracy: 0.78,
          is_current: true,
          is_complete: false
        }}
        history={[
          {
            jar_id: "current",
            week_start_date: "2026-03-09",
            week_end_date: "2026-03-15",
            capacity_stars: 100,
            earned_stars: 42,
            fill_ratio: 0.42,
            study_time_ms: 420000,
            sessions_count: 3,
            average_accuracy: 0.78,
            is_current: true,
            is_complete: false
          },
          {
            jar_id: "older",
            week_start_date: "2026-03-02",
            week_end_date: "2026-03-08",
            capacity_stars: 100,
            earned_stars: 88,
            fill_ratio: 0.88,
            study_time_ms: 760000,
            sessions_count: 5,
            average_accuracy: 0.82,
            is_current: false,
            is_complete: false
          }
        ]}
      />
    );

    expect(screen.getAllByText("42 / 100")).toHaveLength(2);
    expect(screen.getByText("Past weekly jars")).toBeInTheDocument();
    expect(screen.getByText("88 stars")).toBeInTheDocument();
  });

  it("renders reward copy for quiz completion", () => {
    render(
      <StarJarOverview
        currentJar={{
          jar_id: "current",
          week_start_date: "2026-03-09",
          week_end_date: "2026-03-15",
          capacity_stars: 100,
          earned_stars: 55,
          fill_ratio: 0.55,
          study_time_ms: 600000,
          sessions_count: 4,
          average_accuracy: 0.8,
          is_current: true,
          is_complete: false
        }}
        history={[]}
        rewardSummary={{
          week_start_date: "2026-03-09",
          week_end_date: "2026-03-15",
          study_time_ms: 120000,
          accuracy_ratio: 0.75,
          stars_awarded: 9
        }}
        showHistory={false}
      />
    );

    expect(screen.getByTestId("star-jar-reward")).toBeInTheDocument();
    expect(screen.getByText("You earned 9 stars this session.")).toBeInTheDocument();
    expect(screen.getByText(/75% accuracy/i)).toBeInTheDocument();
  });

  it("renders an empty archive state", () => {
    render(<StarJarOverview currentJar={null} history={[]} />);

    expect(screen.getByText("No current jar yet")).toBeInTheDocument();
    expect(screen.getByTestId("star-jar-empty-history")).toBeInTheDocument();
  });
});
