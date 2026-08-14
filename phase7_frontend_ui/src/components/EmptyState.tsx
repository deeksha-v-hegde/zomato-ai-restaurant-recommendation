interface EmptyStateProps {
  message?: string | null;
  hints?: string[];
}

export function EmptyState({ message, hints = [] }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <div className="empty-icon" aria-hidden="true">
        🍽️
      </div>
      <h2>No matches found</h2>
      <p>{message ?? "No restaurants match your preferences."}</p>
      {hints.length > 0 && (
        <div className="hint-box">
          <h3>Try adjusting your search</h3>
          <ul>
            {hints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
