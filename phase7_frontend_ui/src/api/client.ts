import type {
  ApiError,
  CatalogResponse,
  RecommendRequest,
  RecommendResponse,
  ValidationErrorDetail,
} from "../types/api";

const DEFAULT_BACKEND_URL = "https://zomato-ai-backend-yf4c.onrender.com";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? DEFAULT_BACKEND_URL : "")
).replace(/\/$/, "");

async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = await response.json();
    if (Array.isArray(payload.detail)) {
      const details = payload.detail as ValidationErrorDetail[];
      return {
        message: "Please fix the highlighted fields.",
        details,
      };
    }
    if (typeof payload.detail === "string") {
      return { message: payload.detail };
    }
    return { message: response.statusText || "Request failed." };
  } catch {
    return { message: response.statusText || "Request failed." };
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      ...init,
    });
  } catch {
    throw {
      message:
        "Cannot reach the backend API. Start Phase 6 with: python -m phase6_backend_api --reload",
    } satisfies ApiError;
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  return response.json() as Promise<T>;
}

export function fetchLocations(): Promise<CatalogResponse> {
  return request<CatalogResponse>("/catalog/locations");
}

export function fetchCuisines(): Promise<CatalogResponse> {
  return request<CatalogResponse>("/catalog/cuisines");
}

export function recommend(payload: RecommendRequest): Promise<RecommendResponse> {
  return request<RecommendResponse>("/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
