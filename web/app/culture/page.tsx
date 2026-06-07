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
        subtitle="India export lane and global entry points — programming tables from my listening."
      />
      <div className="grid-2">
        <section className="card">
          <h2 className="card-title">Indian artists — export / diaspora</h2>
          <DataTable
            rows={culture.india_export}
            emptyMessage="No India-linked artists in current data."
          />
        </section>
        <section className="card">
          <h2 className="card-title">International → India entry</h2>
          <DataTable
            rows={culture.global_entry}
            emptyMessage="No global-entry lane matches in current data."
          />
        </section>
      </div>
    </>
  );
}
