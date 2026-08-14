import { useCallback, useEffect, useState } from "react";

import { fetchCuisines, fetchLocations, recommend } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { FallbackBanner } from "../components/FallbackBanner";
import { LoadingState } from "../components/LoadingState";
import { PreferenceForm, type PreferenceFormValues } from "../components/PreferenceForm";
import { RecommendationList } from "../components/RecommendationList";
import type { ApiError, RecommendResponse, UiState } from "../types/api";

const DEFAULT_FORM: PreferenceFormValues = {
  location: "Bellandur",
  budget: "high",
  cuisine: "North Indian",
  minRating: "4.0",
  additionalPreferences: "",
  cuisineMatchMode: "or",
};

function mapFieldErrors(error: ApiError): Record<string, string> {
  const mapped: Record<string, string> = {};
  for (const detail of error.details ?? []) {
    mapped[detail.field] = detail.message;
  }
  return mapped;
}

export function Home() {
  const [formValues, setFormValues] = useState<PreferenceFormValues>(DEFAULT_FORM);
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [uiState, setUiState] = useState<UiState>("idle");
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [catalogError, setCatalogError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCatalog() {
      try {
        const [locationData, cuisineData] = await Promise.all([
          fetchLocations(),
          fetchCuisines(),
        ]);
        setLocations(locationData.items);
        setCuisines(cuisineData.items);
      } catch {
        setCatalogError("Could not load location/cuisine catalog. You can still type values manually.");
      }
    }

    void loadCatalog();
  }, []);

  const handleSubmit = useCallback(async () => {
    setUiState("submitting");
    setErrorMessage(null);
    setFieldErrors({});
    setResult(null);

    const payload = {
      location: formValues.location.trim(),
      budget: formValues.budget,
      cuisine: formValues.cuisine.trim(),
      min_rating: Number(formValues.minRating),
      additional_preferences: formValues.additionalPreferences.trim() || undefined,
      cuisine_match_mode: formValues.cuisineMatchMode,
    };

    try {
      const response = await recommend(payload);
      setResult(response);

      if (response.state === "no_match") {
        setUiState("no_match");
      } else {
        setUiState("results");
      }
    } catch (error) {
      const apiError = error as ApiError;
      setErrorMessage(apiError.message ?? "Something went wrong. Please try again.");
      setFieldErrors(mapFieldErrors(apiError));
      setUiState("error");
    }
  }, [formValues]);

  const isSubmitting = uiState === "submitting";

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-content">
          <p className="eyebrow">Zomato AI Recommendations</p>
          <h1>Discover restaurants tailored to your taste</h1>
          <p className="hero-copy">
            Tell us where you want to eat, your budget, and cuisine — our Groq-powered engine
            will rank the best matches with explanations.
          </p>
        </div>
      </header>

      <main className="layout">
        <section className="panel form-panel">
          <h2>Your preferences</h2>
          {catalogError && <p className="inline-notice">{catalogError}</p>}
          <PreferenceForm
            values={formValues}
            locations={locations}
            cuisines={cuisines}
            disabled={isSubmitting}
            fieldErrors={fieldErrors}
            onChange={setFormValues}
            onSubmit={() => void handleSubmit()}
          />
        </section>

        <section className="panel results-panel">
          {isSubmitting && <LoadingState />}

          {!isSubmitting && uiState === "error" && (
            <div className="error-state">
              <h2>Search failed</h2>
              <p>{errorMessage}</p>
              <button type="button" className="secondary-btn" onClick={() => setUiState("idle")}>
                Try again
              </button>
            </div>
          )}

          {!isSubmitting && uiState === "no_match" && (
            <EmptyState message={result?.no_match_message} hints={result?.refine_hints} />
          )}

          {!isSubmitting && uiState === "results" && result && (
            <>
              {(result.used_fallback || result.state === "fallback") && (
                <FallbackBanner reason={result.fallback_reason} />
              )}
              <RecommendationList items={result.recommendations} summary={result.summary} />
              {result.warnings.length > 0 && (
                <div className="warnings-box">
                  <h3>Notes</h3>
                  <ul>
                    {result.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {!isSubmitting && uiState === "idle" && (
            <div className="placeholder-state">
              <h2>Ready when you are</h2>
              <p>Submit your preferences to see AI-ranked restaurant recommendations.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
