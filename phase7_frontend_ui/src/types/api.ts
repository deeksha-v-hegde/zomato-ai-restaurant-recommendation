export type BudgetBand = "low" | "medium" | "high";
export type CuisineMatchMode = "or" | "and";
export type UiState = "idle" | "submitting" | "results" | "no_match" | "error";

export interface RecommendRequest {
  location: string;
  budget: BudgetBand;
  cuisine: string;
  min_rating: number;
  additional_preferences?: string;
  cuisine_match_mode?: CuisineMatchMode;
}

export interface PreferencesSummary {
  location: string;
  location_key: string;
  budget: string;
  cuisines: string[];
  min_rating: number;
}

export interface RecommendationCard {
  rank: number;
  candidate_id: string;
  name: string;
  location: string;
  cuisines: string;
  rating: string;
  cost: string;
  budget_band: string;
  explanation: string;
  source: string;
}

export interface FilterDiagnostics {
  total_records: number;
  after_location: number;
  after_budget: number;
  after_cuisine: number;
  after_rating: number;
  shortlist_count: number;
}

export interface RecommendResponse {
  state: "results" | "no_match" | "fallback";
  preferences: PreferencesSummary | null;
  recommendations: RecommendationCard[];
  summary: string | null;
  used_fallback: boolean;
  fallback_reason: string | null;
  warnings: string[];
  no_match_message: string | null;
  refine_hints: string[];
  filter_diagnostics: FilterDiagnostics | null;
  llm_model: string | null;
}

export interface CatalogResponse {
  count: number;
  items: string[];
}

export interface ValidationErrorDetail {
  field: string;
  message: string;
}

export interface ApiError {
  message: string;
  details?: ValidationErrorDetail[];
}
