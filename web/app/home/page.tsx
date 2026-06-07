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
        subtitle="Editorial positioning and the room-reading that shaped this portfolio."
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
        <h2 className="card-title">How I learned to read a room</h2>
        <p className="body-text">{home.dj_story}</p>
      </section>
      <p className="meta-line">
        Data snapshot: {meta.built_at.slice(0, 10)} · {meta.disclaimer}
      </p>
    </>
  );
}
