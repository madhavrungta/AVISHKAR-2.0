import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchThermalObservations } from "../src/api";

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

