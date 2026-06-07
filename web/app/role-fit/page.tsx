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
        subtitle={`${cv.target_role} — evidence from listening + verified career history.`}
      />
      <p>
        <strong>{cv.name}</strong> · {cv.headline}
        <br />
        <a href={cv.linkedin_url} target="_blank" rel="noreferrer">
          LinkedIn profile
        </a>{" "}
        · {cv.contact}
      </p>
      <section className="card prose">
        <ReactMarkdown>{role_fit.markdown}</ReactMarkdown>
      </section>
      {role_fit.breakout_preview.length > 0 ? (
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Top breakout artists (quick reference)</h2>
          <DataTable rows={role_fit.breakout_preview} />
        </section>
      ) : null}
    </>
  );
}
