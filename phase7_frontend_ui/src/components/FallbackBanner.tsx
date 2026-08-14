interface FallbackBannerProps {
  reason?: string | null;
}

export function FallbackBanner({ reason }: FallbackBannerProps) {
  return (
    <div className="fallback-banner" role="status">
      <strong>AI explanations unavailable.</strong>
      <span>
        {reason
          ? reason
          : "Showing ranked results using rating and popularity instead of Groq."}
      </span>
    </div>
  );
}
