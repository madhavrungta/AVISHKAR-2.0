import { afterEach, describe, expect, it, vi } from "vitest";
import {
  computeAssociations,
  fetchAssociations,
  fetchFacilities,
  fetchThermalObservations,
} from "../src/api";

describe("fetchThermalObservations", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns the API page shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ items: [], total: 0, limit: 2000, offset: 0 }), { status: 200 }),
      ),
    );

    await expect(fetchThermalObservations()).resolves.toMatchObject({ total: 0, items: [] });
  });

  it("surfaces API details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "PostGIS is unavailable." }), { status: 503 })),
    );

    await expect(fetchThermalObservations()).rejects.toThrow("PostGIS is unavailable.");
  });
});

describe("fetchFacilities", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns the facility page shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ items: [], total: 0, limit: 2000, offset: 0 }), { status: 200 }),
      ),
    );

    await expect(fetchFacilities()).resolves.toMatchObject({ total: 0, items: [] });
  });

  it("surfaces API error detail for facilities", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "PostGIS is unavailable." }), { status: 503 }),
      ),
    );

    await expect(fetchFacilities()).rejects.toThrow("PostGIS is unavailable.");
  });

  it("throws generic message when no detail field present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 500 })),
    );

    await expect(fetchFacilities()).rejects.toThrow("API request failed with status 500.");
  });
});

describe("fetchAssociations and computeAssociations", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns associations page shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ items: [], total: 0, limit: 2000, offset: 0 }), { status: 200 }),
      ),
    );

    await expect(fetchAssociations()).resolves.toMatchObject({ total: 0, items: [] });
  });

  it("calls compute endpoint and returns result", async () => {
    const mockResult = {
      evaluated_observations: 10,
      matched_observations: 2,
      total_associations: 3,
      by_type: { very_close: 1, nearby: 2, contextual: 0 },
      radius_meters: 5000,
      computation_timestamp: new Date().toISOString(),
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify(mockResult), { status: 200 })),
    );

    await expect(computeAssociations(5000)).resolves.toMatchObject({
      evaluated_observations: 10,
      total_associations: 3,
    });
  });
});
