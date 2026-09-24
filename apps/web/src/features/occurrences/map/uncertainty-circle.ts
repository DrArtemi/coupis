import type { GeoJSONSource } from "maplibre-gl";

const EARTH_RADIUS_M = 6_371_008.8;
const CIRCLE_SEGMENTS = 64;

export type UncertaintyGeoJSON = Exclude<
  Parameters<GeoJSONSource["setData"]>[0],
  string
>;

export const EMPTY_UNCERTAINTY_GEOJSON: UncertaintyGeoJSON = {
  type: "FeatureCollection",
  features: [],
};

export function createUncertaintyCircle(
  longitude: number,
  latitude: number,
  radiusM: number,
): UncertaintyGeoJSON {
  if (radiusM <= 0) {
    return EMPTY_UNCERTAINTY_GEOJSON;
  }

  const latitudeRadians = (latitude * Math.PI) / 180;
  const longitudeRadians = (longitude * Math.PI) / 180;
  const angularDistance = radiusM / EARTH_RADIUS_M;
  const coordinates: [number, number][] = [];

  for (let index = 0; index <= CIRCLE_SEGMENTS; index += 1) {
    const bearing = (index / CIRCLE_SEGMENTS) * 2 * Math.PI;
    const destinationLatitude = Math.asin(
      Math.sin(latitudeRadians) * Math.cos(angularDistance) +
        Math.cos(latitudeRadians) *
          Math.sin(angularDistance) *
          Math.cos(bearing),
    );
    const destinationLongitude =
      longitudeRadians +
      Math.atan2(
        Math.sin(bearing) *
          Math.sin(angularDistance) *
          Math.cos(latitudeRadians),
        Math.cos(angularDistance) -
          Math.sin(latitudeRadians) * Math.sin(destinationLatitude),
      );

    coordinates.push([
      (((destinationLongitude * 180) / Math.PI + 540) % 360) - 180,
      (destinationLatitude * 180) / Math.PI,
    ]);
  }

  return {
    type: "Feature",
    properties: { radiusM },
    geometry: {
      type: "Polygon",
      coordinates: [coordinates],
    },
  };
}
