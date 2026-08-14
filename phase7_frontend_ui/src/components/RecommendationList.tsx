import type { RecommendationCard as RecommendationCardType } from "../types/api";
import { RecommendationCard } from "./RecommendationCard";

import { formatDisplayText } from "../utils/text";

interface RecommendationListProps {
  items: RecommendationCardType[];
  summary?: string | null;
}

export function RecommendationList({ items, summary }: RecommendationListProps) {
  const summaryText = summary ? formatDisplayText(summary) : null;
  return (
    <section className="recommendation-list">
      <div className="section-heading">
        <h2>Top recommendations</h2>
        <p>{items.length} restaurant{items.length === 1 ? "" : "s"} matched your preferences</p>
      </div>

      {summaryText && <p className="results-summary">{summaryText}</p>}

      <div className="card-grid">
        {items.map((item) => (
          <RecommendationCard key={item.candidate_id} item={item} />
        ))}
      </div>
    </section>
  );
}
