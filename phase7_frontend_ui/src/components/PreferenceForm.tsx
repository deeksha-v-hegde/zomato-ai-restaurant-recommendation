import type { RecommendRequest } from "../types/api";

export interface PreferenceFormValues {
  location: string;
  budget: RecommendRequest["budget"];
  cuisine: string;
  minRating: string;
  additionalPreferences: string;
  cuisineMatchMode: RecommendRequest["cuisine_match_mode"];
}

interface PreferenceFormProps {
  values: PreferenceFormValues;
  locations: string[];
  cuisines: string[];
  disabled?: boolean;
  fieldErrors?: Record<string, string>;
  onChange: (values: PreferenceFormValues) => void;
  onSubmit: () => void;
}

export function PreferenceForm({
  values,
  locations,
  cuisines,
  disabled = false,
  fieldErrors = {},
  onChange,
  onSubmit,
}: PreferenceFormProps) {
  const update = <K extends keyof PreferenceFormValues>(key: K, value: PreferenceFormValues[K]) => {
    onChange({ ...values, [key]: value });
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="preference-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <label className="field">
          <span>Location</span>
          <input
            list="location-options"
            value={values.location}
            onChange={(e) => update("location", e.target.value)}
            placeholder="e.g. Bellandur"
            disabled={disabled}
            required
          />
          <datalist id="location-options">
            {locations.map((location) => (
              <option key={location} value={location} />
            ))}
          </datalist>
          {fieldErrors.location && <small className="field-error">{fieldErrors.location}</small>}
        </label>

        <label className="field">
          <span>Budget</span>
          <select
            value={values.budget}
            onChange={(e) => update("budget", e.target.value as PreferenceFormValues["budget"])}
            disabled={disabled}
            required
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          {fieldErrors.budget && <small className="field-error">{fieldErrors.budget}</small>}
        </label>

        <label className="field">
          <span>Cuisine</span>
          <input
            list="cuisine-options"
            value={values.cuisine}
            onChange={(e) => update("cuisine", e.target.value)}
            placeholder="e.g. North Indian"
            disabled={disabled}
            required
          />
          <datalist id="cuisine-options">
            {cuisines.map((cuisine) => (
              <option key={cuisine} value={cuisine} />
            ))}
          </datalist>
          {fieldErrors.cuisine && <small className="field-error">{fieldErrors.cuisine}</small>}
        </label>

        <label className="field">
          <span>Minimum rating</span>
          <input
            type="number"
            min="0"
            max="5"
            step="0.1"
            value={values.minRating}
            onChange={(e) => update("minRating", e.target.value)}
            disabled={disabled}
            required
          />
          {fieldErrors.min_rating && (
            <small className="field-error">{fieldErrors.min_rating}</small>
          )}
        </label>

        <label className="field">
          <span>Cuisine match</span>
          <select
            value={values.cuisineMatchMode ?? "or"}
            onChange={(e) =>
              update("cuisineMatchMode", e.target.value as PreferenceFormValues["cuisineMatchMode"])
            }
            disabled={disabled}
          >
            <option value="or">Any selected cuisine (OR)</option>
            <option value="and">All selected cuisines (AND)</option>
          </select>
        </label>
      </div>

      <label className="field field-full">
        <span>Additional preferences (optional)</span>
        <textarea
          value={values.additionalPreferences}
          onChange={(e) => update("additionalPreferences", e.target.value)}
          placeholder="Family-friendly, quick service, budget around 2000 for two..."
          rows={3}
          disabled={disabled}
        />
      </label>

      <button type="submit" className="submit-btn" disabled={disabled}>
        {disabled ? "Finding recommendations…" : "Get recommendations"}
      </button>
    </form>
  );
}
