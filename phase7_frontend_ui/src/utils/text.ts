/** Decode HTML entities returned by Phase 6 display normalizer (OD-04). */
export function decodeHtmlEntities(text: string): string {
  if (!text) return text;
  const textarea = document.createElement("textarea");
  textarea.innerHTML = text;
  return textarea.value;
}

export function formatDisplayText(text: string | null | undefined, fallback = "N/A"): string {
  if (!text || !text.trim()) return fallback;
  return decodeHtmlEntities(text.trim());
}
