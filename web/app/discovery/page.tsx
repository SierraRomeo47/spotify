import { DiscoveryClient } from "@/components/DiscoveryClient";
import { PageHeader } from "@/components/PageHeader";
import { getPortfolio } from "@/lib/portfolio";

export default function DiscoveryPage() {
  const data = getPortfolio();
  const d = data.discovery;

  return (
    <>
      <PageHeader
        title="Discovery"
        subtitle="Artists you're leaning into before they become long-term staples — from your listening, not chart data."
      />
      <DiscoveryClient
        watchlistAll={d.watchlist_all}
        metrics={d.metrics}
        dailyPlays={d.daily_plays}
        trackWatchlist={d.track_watchlist}
        chartDaily={d.chart_daily}
        audioProfile={d.audio_profile}
      />
    </>
  );
}
