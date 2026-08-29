import { useCallback, useEffect, useState } from "react";
import {
  computeAssociations,
  fetchAssociationSummary,
  fetchFacilities,
  fetchThermalObservations,
} from "./api";
import { MapPanel } from "./components/MapPanel";
import type {
  AssociationSummary,
  FacilityPage,
  ThermalObservationPage,
} from "./types";

export function App() {
  const [obsPage, setObsPage] = useState<ThermalObservationPage | null>(null);
  const [facPage, setFacPage] = useState<FacilityPage | null>(null);
  const [assocSummary, setAssocSummary] = useState<AssociationSummary | null>(null);

  const [obsError, setObsError] = useState<string | null>(null);
  const [facError, setFacError] = useState<string | null>(null);
  const [assocError, setAssocError] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [computeStatus, setComputeStatus] = useState<string | null>(null);

  const loadAll = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setObsError(null);
    setFacError(null);
    setAssocError(null);

    const [obsResult, facResult, assocResult] = await Promise.allSettled([
      fetchThermalObservations(signal),
      fetchFacilities(signal),
      fetchAssociationSummary(signal),
    ]);

    if (obsResult.status === "fulfilled") {
      setObsPage(obsResult.value);
    } else if (
      !(obsResult.reason instanceof DOMException && obsResult.reason.name === "AbortError")
    ) {
      setObsError(
        obsResult.reason instanceof Error
          ? obsResult.reason.message
          : "Unable to load thermal anomalies.",
      );
    }

    if (facResult.status === "fulfilled") {
      setFacPage(facResult.value);
    } else if (
      !(facResult.reason instanceof DOMException && facResult.reason.name === "AbortError")
    ) {
      setFacError(
        facResult.reason instanceof Error
          ? facResult.reason.message
          : "Unable to load industrial facilities.",
      );
    }

    if (assocResult.status === "fulfilled") {
      setAssocSummary(assocResult.value);
    } else if (
      !(assocResult.reason instanceof DOMException && assocResult.reason.name === "AbortError")
    ) {
      setAssocError(
        assocResult.reason instanceof Error
          ? assocResult.reason.message
          : "Unable to load association summary.",
      );
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadAll(controller.signal);
    return () => controller.abort();
  }, [loadAll]);

  const handleComputeAssociations = async () => {
    setComputing(true);
    setComputeStatus(null);
    try {
      const result = await computeAssociations(5000);
      setComputeStatus(
        `Computation complete: ${result.total_associations} spatial candidates generated across ${result.evaluated_observations} observations.`,
      );
      void loadAll();
    } catch (err) {
      setComputeStatus(
        `Computation failed: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
    } finally {
      setComputing(false);
    }
  };

  const observations = obsPage?.items ?? [];
  const facilities = facPage?.items ?? [];

  return (
    <main className="min-h-screen bg-ivory text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gold">
              SIH 26162 · Phase 3
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
              Spatial Association of Thermal Anomalies &amp; Industrial Facilities
            </h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              PostGIS spatial proximity candidate analysis. Spatial association indicates geographic co-location
              within the search radius and does not constitute a confirmed industrial fire.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="rounded-md bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => void handleComputeAssociations()}
              disabled={computing || loading || observations.length === 0}
            >
              {computing ? "Computing…" : "⚡ Compute Associations"}
            </button>
            <button
              type="button"
              className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-gold focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => void loadAll()}
              disabled={loading || computing}
            >
              {loading ? "Loading…" : "Refresh data"}
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-5 py-6">
        {/* Counters */}
        <div className="mb-4 flex flex-wrap items-center gap-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Thermal Anomalies</p>
            <p className="text-xl font-bold text-[#dc5a24]">
              🔥 {obsPage ? obsPage.total.toLocaleString() : "—"}
            </p>
          </div>
          <div className="border-l border-slate-200 pl-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Industrial Facilities</p>
            <p className="text-xl font-bold text-[#1d6fa4]">
              🏭 {facPage ? facPage.total.toLocaleString() : "—"}
            </p>
          </div>
          <div className="border-l border-slate-200 pl-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Spatial Associations</p>
            <p className="text-xl font-bold text-rose-600">
              🔗 {assocSummary ? assocSummary.total_associations.toLocaleString() : "0"}
            </p>
          </div>
          {assocSummary && assocSummary.total_associations > 0 && (
            <div className="border-l border-slate-200 pl-6 text-xs text-slate-600">
              <span className="font-medium text-slate-700">Breakdown:</span>{" "}
              {assocSummary.by_type.very_close ?? 0} very close · {assocSummary.by_type.nearby ?? 0} nearby ·{" "}
              {assocSummary.by_type.contextual ?? 0} contextual
            </div>
          )}
        </div>

        {/* Status banner */}
        {computeStatus ? (
          <div role="status" className="mb-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
            {computeStatus}
          </div>
        ) : null}

        {/* Error alerts */}
        {obsError ? (
          <div role="alert" className="mb-3 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
            <p className="font-semibold">Thermal anomaly data is unavailable.</p>
            <p className="mt-1">{obsError}</p>
          </div>
        ) : null}
        {facError ? (
          <div role="alert" className="mb-3 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Industrial facility data is unavailable.</p>
            <p className="mt-1">{facError}</p>
          </div>
        ) : null}
        {assocError ? (
          <div role="alert" className="mb-3 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Spatial association summary is unavailable.</p>
            <p className="mt-1">{assocError}</p>
          </div>
        ) : null}

        {/* Empty states */}
        {!loading && !obsError && observations.length === 0 ? (
          <div className="mb-3 rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-700">
            No validated FIRMS thermal anomalies are stored yet. Run FIRMS ingestion to populate this layer.
          </div>
        ) : null}
        {!loading && !facError && facilities.length === 0 ? (
          <div className="mb-3 rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-700">
            No industrial facilities found. Run <code className="font-mono text-xs">POST /ingestion/osm</code> to populate this layer.
          </div>
        ) : null}

        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-slate-100 shadow-sm">
          <MapPanel observations={observations} facilities={facilities} />
        </div>
      </section>
    </main>
  );
}
