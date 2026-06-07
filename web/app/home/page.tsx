import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";
import ReactMarkdown from "react-markdown";

export default function HomePage() {
  const data = getPortfolio();
  const { home, meta } = data;

  return (
    <>
      <PageHeader
        title="Home"
        subtitle="Positioning and DJ narrative — Sierra Romeo Editorial Intelligence Lab."
      />
      <div className="pills">
        {home.role_pills.map((p) => (
          <span key={p} className="pill">
            {p}
          </span>
        ))}
      </div>
      <section className="card prose">
        <ReactMarkdown>{home.intro_markdown}</ReactMarkdown>
      </section>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Your DJ story</h2>
        <p style={{ color: "var(--muted)", whiteSpace: "pre-wrap" }}>{home.dj_story}</p>
      </section>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
        Data snapshot: {meta.built_at.slice(0, 10)} · {meta.disclaimer}
      </p>
    </>
  );
}
