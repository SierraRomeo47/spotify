import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";

export default function CulturePage() {
  const data = getPortfolio();
  const { culture } = data;

  return (
    <>
      <PageHeader
        title="Culture & programming lanes"
        subtitle="Club/electronic discovery + India ↔ global hip-hop — programming tables."
      />
      <div className="grid-2">
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Indian artists — export / diaspora lane</h2>
          <DataTable
            rows={culture.india_export}
            emptyMessage="No India-linked artists in current data."
          />
        </section>
        <section className="card">
          <h2 style={{ marginTop: 0 }}>International → India entry points</h2>
          <DataTable
            rows={culture.global_entry}
            emptyMessage="No global-entry lane matches in current data."
          />
        </section>
      </div>
    </>
  );
}
