"use client";

import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function MeteoriteGamePage() {
  const searchParams = useSearchParams();
  const lectureId = searchParams.get("lectureId");

  useEffect(() => {
    if (!lectureId) return;

    // Load the Unity WebGL build dynamically
    const container = document.getElementById("unity-container");
    if (container) {
      const iframe = document.createElement("iframe");
      iframe.src = `/unity/index.html?lectureId=${lectureId}`;
      iframe.width = "960";
      iframe.height = "600";
      iframe.style.border = "none";
      container.appendChild(iframe);
    }
  }, [lectureId]);

  return (
    <div>
      {!lectureId && <p>Error: lectureId missing</p>}
      <div id="unity-container"></div>
    </div>
  );
}