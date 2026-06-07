import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";
import ReactMarkdown from "react-markdown";

export default function CuratePage() {
  const data = getPortfolio();
  const { curate } = data;
  const t = curate.tenure;
  const m = t.metrics;

  return (
    <>
      <PageHeader
        title="Curate"
        subtitle="Listening profile, playlist sequencing proof, and playlist scores."
      />

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Listening tenure</h2>
        <div className="metrics">
          <div className="metric">
            <label>Years on Spotify</label>
            <strong>~{m.years_on_spotify ?? "—"}</strong>
          </div>
          <div className="metric">
            <label>Unique songs (merged)</label>
            <strong>{m.unique_songs_merged ?? "—"}</strong>
          </div>
          <div className="metric">
            <label>Artists (catalog)</label>
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
          <h2 style={{ marginTop: 0 }}>{concept}</h2>
          <p style={{ color: "var(--muted)" }}>{seq.narrative}</p>
          <DataTable rows={seq.tracks} emptyMessage="No sequence rows." />
        </section>
      ))}

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Your playlists (top scores)</h2>
        <DataTable rows={curate.playlist_scores} emptyMessage="No playlist scores." />
      </section>

      {t.long_term_tracks.length > 0 ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>All-time top tracks</h2>
          <DataTable rows={t.long_term_tracks.slice(0, 25)} />
        </section>
      ) : null}
    </>
  );
}
