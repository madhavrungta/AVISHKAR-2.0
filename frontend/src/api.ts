import type {
  AssociationComputeResult,
  AssociationPage,
  AssociationSummary,
  FacilityPage,
  ThermalFacilityAssociation,
  ThermalObservationPage,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    signal,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : `API request failed with status ${response.status}.`;
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function fetchThermalObservations(
  signal?: AbortSignal,
): Promise<ThermalObservationPage> {
  return apiFetch<ThermalObservationPage>("/thermal-observations?limit=2000", undefined, signal);
}

export async function fetchFacilities(
  signal?: AbortSignal,
): Promise<FacilityPage> {
  return apiFetch<FacilityPage>("/facilities?limit=2000", undefined, signal);
}

export async function fetchAssociations(
  signal?: AbortSignal,
): Promise<AssociationPage> {
  return apiFetch<AssociationPage>("/associations?limit=2000", undefined, signal);
}

export async function fetchObservationAssociations(
  observationId: string,
  signal?: AbortSignal,
): Promise<ThermalFacilityAssociation[]> {
  return apiFetch<ThermalFacilityAssociation[]>(
    `/thermal-observations/${observationId}/associations`,
    undefined,
    signal,
  );
}

export async function fetchFacilityAssociations(
  facilityId: string,
  signal?: AbortSignal,
): Promise<ThermalFacilityAssociation[]> {
  return apiFetch<ThermalFacilityAssociation[]>(
    `/facilities/${facilityId}/thermal-observations`,
    undefined,
    signal,
  );
}

export async function computeAssociations(
  radiusMeters?: number,
  observationId?: string,
  signal?: AbortSignal,
): Promise<AssociationComputeResult> {
  return apiFetch<AssociationComputeResult>(
    "/associations/compute",
    {
      method: "POST",
      body: JSON.stringify({
        radius_meters: radiusMeters,
        observation_id: observationId,
      }),
    },
    signal,
  );
}

export async function fetchAssociationSummary(
  signal?: AbortSignal,
): Promise<AssociationSummary> {
  return apiFetch<AssociationSummary>("/analytics/associations/summary", undefined, signal);
}
