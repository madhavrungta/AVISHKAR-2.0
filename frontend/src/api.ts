import type { ThermalObservationPage } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchThermalObservations(
  signal?: AbortSignal,
): Promise<ThermalObservationPage> {
  const response = await fetch(`${API_BASE_URL}/thermal-observations?limit=2000`, { signal });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : `API request failed with status ${response.status}.`;
    throw new Error(detail);
  }
  return (await response.json()) as ThermalObservationPage;
}

