"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function PlotlyChart({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return null;
  const fig = data as { data?: object[]; layout?: Record<string, unknown> };
  return (
    <Plot
      data={fig.data ?? []}
      layout={{
        ...fig.layout,
        autosize: true,
        paper_bgcolor: "#000000",
        plot_bgcolor: "#181818",
        font: { color: "#ffffff" },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: 320 }}
      useResizeHandler
    />
  );
}
