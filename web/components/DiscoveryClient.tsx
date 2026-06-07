"use client";

import { useMemo, useState } from "react";
import { DataTable } from "./DataTable";
import { PlotlyChart } from "./PlotlyChart";

type Row = Record<string, unknown>;

export function DiscoveryClient({
  watchlistAll,
  metrics,
  dailyPlays,
  trackWatchlist,
  chartDaily,
  audioProfile,
}: {
  watchlistAll: Row[];
  metrics: Record<string, number>;
  dailyPlays: Row[];
  trackWatchlist: Row[];
  chartDaily: Record<string, unknown> | null;
  audioProfile: Record<string, unknown>;
}) {
  const [filter, setFilter] = useState("all");

  const filtered = useMemo(() => {
    if (filter === "all") return watchlistAll;
    if (filter === "pre_long_term") {
      return watchlistAll.filter((r) => r.is_pre_long_term === true);
    }
    if (filter === "hiphop_indie") {
      return watchlistAll.filter((r) => {
        const genre = String(r.genre || r.genre_bucket || "");
        const region = String(r.region || r.region_tag || "");
        return genre.includes("Hip-Hop") || region.includes("India");
      });
    }
    return watchlistAll;
  }, [watchlistAll, filter]);

  return (
    <>
      <div className="metrics">
        <div className="metric">
          <label>Pre-long-term artists</label>
          <strong>{metrics.new_artists_pre_long_term ?? "—"}</strong>
        </div>
        <div className="metric">
          <label>Artists in window</label>
          <strong>{metrics.unique_artists_in_window ?? "—"}</strong>
        </div>
      </div>

      <select
        className="filter"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        aria-label="Watchlist filter"
      >
        <option value="all">All artists</option>
        <option value="hiphop_indie">Hip-hop & indie (catalog)</option>
        <option value="pre_long_term">Pre-long-term only</option>
      </select>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Breakout artist watchlist</h2>
        <DataTable rows={filtered.slice(0, 30)} emptyMessage="No watchlist rows for this filter." />
      </section>

      {chartDaily ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Plays per day</h2>
          <PlotlyChart data={chartDaily} />
        </section>
      ) : null}

      {dailyPlays.length > 0 ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Daily log</h2>
          <DataTable rows={dailyPlays} />
        </section>
      ) : null}

      {trackWatchlist.length > 0 ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Track watchlist</h2>
          <DataTable rows={trackWatchlist} />
        </section>
      ) : null}

      {audioProfile && Object.keys(audioProfile).length > 0 ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Audio profile (Exportify)</h2>
          <div className="metrics">
            <div className="metric">
              <label>Median tempo</label>
              <strong>{String(audioProfile.median_tempo ?? "—")}</strong>
            </div>
            <div className="metric">
              <label>Median energy</label>
              <strong>{String(audioProfile.median_energy ?? "—")}</strong>
            </div>
            <div className="metric">
              <label>Median danceability</label>
              <strong>{String(audioProfile.median_danceability ?? "—")}</strong>
            </div>
            <div className="metric">
              <label>Tracks sampled</label>
              <strong>{String(audioProfile.track_count ?? "—")}</strong>
            </div>
          </div>
        </section>
      ) : null}
    </>
  );
}
