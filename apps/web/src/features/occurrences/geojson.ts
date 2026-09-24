import type { GeoJSONSource } from "maplibre-gl";

import type { Occurrence } from "./types";

export type OccurrenceGeoJSON = Exclude<
  Parameters<GeoJSONSource["setData"]>[0],
  string
>;

export function occurrencesToGeoJSON(
  occurrences: readonly Occurrence[],
): OccurrenceGeoJSON {
  return {
    type: "FeatureCollection",
    features: occurrences.map((occurrence) => ({
      type: "Feature",
      id: occurrence.id,
      geometry: {
        type: "Point",
        coordinates: [occurrence.longitude, occurrence.latitude],
      },
      properties: {
        id: occurrence.id,
        gbifId: occurrence.gbif_id,
        observedAt: occurrence.observed_at,
        locality: occurrence.locality,
        uncertaintyM: occurrence.coordinate_uncertainty_m,
        basisOfRecord: occurrence.basis_of_record,
      },
    })),
  };
}
