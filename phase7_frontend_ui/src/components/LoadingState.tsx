export function LoadingState() {
  return (
    <section className="loading-state" aria-live="polite" aria-busy="true">
      <div className="spinner" />
      <h2>Finding recommendations</h2>
      <p>Our AI is ranking restaurants that match your preferences. This may take a few seconds.</p>
    </section>
  );
}
