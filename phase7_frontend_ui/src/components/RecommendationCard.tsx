import type { RecommendationCard as RecommendationCardType } from "../types/api";
import { formatDisplayText } from "../utils/text";

interface RecommendationCardProps {
  item: RecommendationCardType;
}

const SAMPLE_IMAGES = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=800&q=80",
];

const OFFERS = [
  "Flat 15% OFF on Dine-in via Zomato Gold",
  "Complimentary Beer Sampler Tasting Tray",
  "20% OFF on Dim Sum & Cocktail Combos",
  "Flat ₹200 Cashback on Zomato Pay",
  "Free Chef's Dessert Special",
];

export function RecommendationCard({ item }: RecommendationCardProps) {
  const matchPct = Math.max(99 - (item.rank - 1) * 7, 80);
  const imgUrl = SAMPLE_IMAGES[(item.rank - 1) % SAMPLE_IMAGES.length];
  const offerText = OFFERS[(item.rank - 1) % OFFERS.length];
  const cuisines = formatDisplayText(item.cuisines).split(",").slice(0, 4);

  return (
    <div className="top5-card-container">
      {/* Left Column: Photograph & Badges */}
      <div className="left-image-wrapper">
        <img src={imgUrl} alt={formatDisplayText(item.name)} />
        {item.rank === 1 ? (
          <div className="badge-rank-gold">👑 #1 TOP MATCH</div>
        ) : (
          <div className="badge-rank-dark">#{item.rank} RECOMMENDED</div>
        )}
        <div className="bookmark-icon">🔖</div>
        <div className="offer-banner-overlay">🎁 {offerText}</div>
      </div>

      {/* Right Column: Content & AI Breakdown */}
      <div className="card-right-content">
        <div className="card-top-row">
          <h2>
            {formatDisplayText(item.name)} <span className="bookmark-inline">🔖</span>
          </h2>
          <div className="badges-row">
            <span className="rating-badge">★ {formatDisplayText(item.rating)}</span>
            <span className="match-badge">💯 {matchPct}% Match</span>
          </div>
        </div>

        <div className="card-meta-line">
          📍 {formatDisplayText(item.location)} • Bengaluru &nbsp;&nbsp;|&nbsp;&nbsp;
          {cuisines.map((c, i) => (
            <span key={i} className="cat-pill">{c.trim()}</span>
          ))}
          &nbsp;&nbsp;•&nbsp; 💰 {formatDisplayText(item.cost)} &nbsp;•&nbsp; ⏱️ 35 mins
        </div>

        <div className="why-gemini-box">
          <div className="why-gemini-title">🔥 Why Gemini Picked This:</div>
          <p className="explanation-text">{formatDisplayText(item.explanation)}</p>
          <div className="palate-matrix-grid">
            <div className="palate-item">🍽️ <b>Cuisine Affinity:</b> Match with {formatDisplayText(item.cuisines)}</div>
            <div className="palate-item">💰 <b>Budget Fit:</b> {formatDisplayText(item.budget_band)} Band</div>
            <div className="palate-item">💃 <b>Vibe & Setting:</b> Energetic Dining Atmosphere</div>
            <div className="palate-item">📜 <b>History Resonance:</b> Matches top dining history</div>
          </div>
        </div>

        <div className="must-try-row">
          <span className="must-try-label">👌 Must-Try:</span>
          <span className="dish-pill">🍽️ Chef's Special</span>
          <span className="dish-pill">🍽️ Woodfired Specialty</span>
          <span className="dish-pill">🍽️ Signature Beverage</span>
        </div>

        <div className="insider-secret-box">
          💡 <b>Insider Secret:</b> Reserve outdoor terrace seating right before sunset for panoramic skyline views paired with signature dishes.
        </div>

        <div className="card-action-bar">
          <a href="#" className="menu-link">Full Menu & Details ↗</a>
          <div className="action-buttons">
            <button className="action-btn-secondary">🛵 Order Online</button>
            <button className="action-btn-primary">📖 Book Table</button>
          </div>
        </div>
      </div>
    </div>
  );
}
