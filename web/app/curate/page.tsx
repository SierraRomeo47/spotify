import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";
import ReactMarkdown from "react-markdown";

export default function CuratePage() {
  const data = getPortfolio();
  const { curate } = data;
  const t = curate.tenure;
  const m = t.metrics;
  const longTermCols = t.long_term_track_columns?.length
    ? t.long_term_track_columns
    : undefined;

  return (
    <>
      <PageHeader
        title="Curate"
        subtitle="How I sequence a set and score my own playlists."
      />

      <section className="card">
        <h2 className="card-title">
          Listening tenure
          {m.years_on_spotify ? ` (~${m.years_on_spotify} years on Spotify)` : ""}
        </h2>
        <div className="metrics">
          <div className="metric">
            <label>Years on Spotify</label>
            <strong>~{m.years_on_spotify ?? "—"}</strong>
          </div>
          <div className="metric">
            <label>Unique songs</label>
            <strong>{m.unique_songs_merged ?? "—"}</strong>
          </div>
          <div className="metric">
            <label>Artists in catalog</label>
            <strong>{m.unique_artists_catalog ?? "—"}</strong>
          </div>
          <div className="metric">
            <label>All-time top tracks</label>
            <strong>{m.long_term_track_count ?? "—"}</strong>
          </div>
        </div>
        <div className="prose">
          <ReactMarkdown>{t.narrative}</ReactMarkdown>
        </div>
      </section>

      {Object.entries(curate.sequences).map(([concept, seq]) => (
        <section key={concept} className="card">
          <h2 className="card-title">{concept}</h2>
          <div className="prose">
            <ReactMarkdown>{seq.narrative}</ReactMarkdown>
          </div>
          <DataTable
            rows={seq.tracks}
            columns={[
              "sequence_order",
              "role",
              "track",
              "artist",
              "reason_for_placement",
            ]}
            emptyMessage="No sequence rows."
          />
        </section>
      ))}

      <section className="card">
        <h2 className="card-title">Your playlists (top scores)</h2>
        <p className="card-lead">Ranked by discovery, cohesion, and India–global bridge scores.</p>
        <DataTable rows={curate.playlist_scores} emptyMessage="No playlist scores." />
      </section>

      {t.long_term_tracks.length > 0 ? (
        <section className="card">
          <h2 className="card-title">All-time top tracks</h2>
          <p className="card-lead">Long-term taste anchor — employer-facing columns only.</p>
          <DataTable
            rows={t.long_term_tracks.slice(0, 25)}
            columns={longTermCols}
          />
        </section>
      ) : null}
    </>
  );
}
