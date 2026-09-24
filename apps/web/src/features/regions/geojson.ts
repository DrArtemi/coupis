import type { GeoJSONSource } from "maplibre-gl";

import type { Region } from "./types";

export type RegionsGeoJSON = Exclude<
  Parameters<GeoJSONSource["setData"]>[0],
  string
>;

export function regionsToGeoJSON(
  regions: readonly Region[],
): RegionsGeoJSON {
  return {
    type: "FeatureCollection",
    features: regions.map((region) => ({
      type: "Feature",
      id: `${region.slug}:${region.version}`,
      geometry: region.geometry,
      properties: {
        slug: region.slug,
        name: region.name,
        version: region.version,
        source: region.source,
        license: region.license,
      },
    })),
  };
}
