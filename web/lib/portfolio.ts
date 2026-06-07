import fs from "fs";
import path from "path";

export type PortfolioData = {
  meta: {
    built_at: string;
    data_source: string;
    exportify_stats: Record<string, number>;
    disclaimer: string;
    role_workflow: string;
  };
  home: {
    dj_story: string;
    cv: Record<string, string>;
    role_pills: string[];
    intro_markdown: string;
  };
  role_fit: {
    markdown: string;
    breakout_preview: Record<string, unknown>[];
  };
  discovery: {
    metrics: Record<string, number>;
    watchlist_all: Record<string, unknown>[];
    daily_plays: Record<string, unknown>[];
    track_watchlist: Record<string, unknown>[];
    chart_daily: Record<string, unknown> | null;
    audio_profile: Record<string, unknown>;
  };
  culture: {
    india_export: Record<string, unknown>[];
    global_entry: Record<string, unknown>[];
  };
  curate: {
    tenure: {
      metrics: Record<string, number>;
      narrative: string;
      genre_divisions: Record<string, unknown>[];
      region_divisions: Record<string, unknown>[];
      scene_divisions: Record<string, unknown>[];
      long_term_tracks: Record<string, unknown>[];
    };
    playlist_scores: Record<string, unknown>[];
    sequences: Record<
      string,
      { narrative: string; tracks: Record<string, unknown>[] }
    >;
  };
};

export function getPortfolio(): PortfolioData {
  const filePath = path.join(process.cwd(), "public", "data", "portfolio.json");
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as PortfolioData;
}
