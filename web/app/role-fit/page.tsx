import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";
import ReactMarkdown from "react-markdown";

export default function RoleFitPage() {
  const data = getPortfolio();
  const { role_fit, home } = data;
  const cv = home.cv;

  return (
    <>
      <PageHeader
        title="Role Fit Summary"
        subtitle={`${cv.target_role} — listening evidence and verified career history.`}
      />
      <div className="contact-strip">
        <strong>{cv.name}</strong> · {cv.headline}
        <br />
        <a href={cv.linkedin_url} target="_blank" rel="noreferrer">
          LinkedIn profile
        </a>{" "}
        · {cv.contact}
      </div>
      <section className="card prose">
        <ReactMarkdown>{role_fit.markdown}</ReactMarkdown>
      </section>
      {role_fit.breakout_preview.length > 0 ? (
        <section className="card">
          <h2 className="card-title">Top breakout artists</h2>
          <p className="card-lead">Quick reference from the discovery watchlist.</p>
          <DataTable rows={role_fit.breakout_preview} />
        </section>
      ) : null}
    </>
  );
}
