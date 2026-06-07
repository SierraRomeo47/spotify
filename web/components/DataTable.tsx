export function DataTable({
  rows,
  columns,
  emptyMessage = "No data.",
}: {
  rows: Record<string, unknown>[];
  columns?: string[];
  emptyMessage?: string;
}) {
  if (!rows.length) {
    return <p style={{ color: "var(--muted)" }}>{emptyMessage}</p>;
  }

  const denylist = new Set([
    "track_id",
    "artist_id",
    "album_id",
    "playlist_id",
    "uri",
    "track_uri",
    "artist_uri",
    "album_uri",
    "duration_ms",
    "time_range",
    "is_pre_long_term",
    "is_pre_long_term_artist",
    "editorial_note",
    "_key",
    "terms_present",
    "listen_velocity",
    "velocity_score",
  ]);

  const cols =
    columns && columns.length
      ? columns
      : Object.keys(rows[0]).filter((k) => !k.startsWith("_") && !denylist.has(k));

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{formatHeader(c)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>{formatCell(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const HEADER_LABELS: Record<string, string> = {
  track_name: "Track",
  artist_name: "Artist",
  genre_bucket: "Genre",
  region_tag: "Region",
  scene_tag: "Scene",
  release_year: "Year",
  release_date: "Release",
  duration_min: "Length (min)",
  early_discovery_score: "Discovery score",
  programming_lane: "Lane",
  editorial_action: "Editor note",
  listen_count: "Listens",
  first_detected_date: "First heard",
  popularity_band: "Popularity",
  sequence_order: "Order",
  reason_for_placement: "Placement",
  play_date: "Date",
  total_plays: "Plays",
  unique_artists: "Artists",
  new_artists: "New artists",
  top_artist_that_day: "Top artist",
  cohesion_score: "Cohesion",
  discovery_score: "Discovery",
  recency_score: "Recency",
  india_global_bridge_score: "India–global",
  track_count: "Tracks",
  division: "Division",
  count: "Count",
};

function formatHeader(key: string): string {
  if (HEADER_LABELS[key]) return HEADER_LABELS[key];
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCell(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(1);
  return String(v);
}
