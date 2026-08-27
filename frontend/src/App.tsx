import { useCallback, useEffect, useState } from "react";
import { fetchThermalObservations } from "./api";
import { MapPanel } from "./components/MapPanel";
import type { ThermalObservationPage } from "./types";

export function App() {
  const [page, setPage] = useState<ThermalObservationPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadObservations = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      setPage(await fetchThermalObservations(signal));
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }
      setError(caught instanceof Error ? caught.message : "Unable to load thermal anomalies.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadObservations(controller.signal);
    return () => controller.abort();
  }, [loadObservations]);

  const observations = page?.items ?? [];
  return (
    <main className="min-h-screen bg-ivory text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gold">SIH 26162 · Phase 1</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">NASA FIRMS Thermal Anomalies</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              Visual validation only. Points are satellite thermal anomalies—not confirmed fires or industrial classifications.
            </p>
          </div>
          <button
            type="button"
            className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-gold focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={() => void loadObservations()}
            disabled={loading}
          >
            {loading ? "Loading…" : "Refresh data"}
          </button>
        </div>
      </header>
      <section className="mx-auto max-w-7xl px-5 py-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-slate-700">
            {page ? `${page.total.toLocaleString()} stored thermal anomalies` : "Stored thermal anomalies"}
          </p>
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-900">NASA FIRMS layer</span>
        </div>
        {error ? (
          <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
            <p className="font-semibold">Map data is unavailable.</p>
            <p className="mt-1">{error}</p>
          </div>
        ) : null}
        {!loading && !error && observations.length === 0 ? (
          <div className="rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-700">
            No validated FIRMS thermal anomalies are stored yet. Configure a MAP_KEY and run an ingestion to populate this map.
          </div>
        ) : null}
        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-slate-100 shadow-sm">
          <MapPanel observations={observations} />
        </div>
      </section>
    </main>
  );
}

