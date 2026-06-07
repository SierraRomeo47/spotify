import type { Metadata } from "next";
import { SiteNav } from "@/components/SiteNav";
import { getPortfolio } from "@/lib/portfolio";
import { APP_TITLE } from "@/lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  title: APP_TITLE,
  description: "Editorial intelligence portfolio — discovery, culture, curate, role fit.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  let footerMeta = "";
  try {
    const data = getPortfolio();
    const built = data.meta.built_at.slice(0, 19).replace("T", " ");
    footerMeta = `Snapshot: ${built} UTC · Source: ${data.meta.data_source}`;
  } catch {
    footerMeta = "Run python scripts/build_site_data.py to generate data.";
  }

  return (
    <html lang="en">
      <body>
        <div className="site-shell">
          <SiteNav />
          <main className="site-main">{children}</main>
          <footer className="site-footer">
            <div>{footerMeta}</div>
            <div>Portfolio project using authorized personal listening data; not affiliated with Spotify.</div>
          </footer>
        </div>
      </body>
    </html>
  );
}
