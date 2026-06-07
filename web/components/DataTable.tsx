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
  const cols =
    columns && columns.length
      ? columns
      : Object.keys(rows[0]).filter((k) => !k.startsWith("_"));

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c.replace(/_/g, " ")}</th>
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

function formatCell(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(1);
  return String(v);
}
