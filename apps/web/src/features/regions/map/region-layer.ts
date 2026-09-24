import {
  type GeoJSONSource,
  LngLatBounds,
  type Map as MapLibreMap,
  type MapLayerMouseEvent,
} from "maplibre-gl";

import { regionsToGeoJSON } from "../geojson";
import type { Region } from "../types";

const REGION_SOURCE_ID = "regions";
const REGION_FILL_LAYER_ID = "regions-fill";
const SELECTED_REGION_FILL_LAYER_ID = "selected-region-fill";
const REGION_OUTLINE_LAYER_ID = "regions-outline";
const SELECTED_REGION_OUTLINE_LAYER_ID = "selected-region-outline";

type MapFilter = NonNullable<Parameters<MapLibreMap["setFilter"]>[1]>;

type RegionLayerOptions = {
  onSelect: (region: Region) => void;
};

export type RegionLayerController = {
  setRegions: (regions: readonly Region[]) => void;
  setSelectedRegion: (region: Region | null) => void;
  destroy: () => void;
};

function selectedRegionFilter(region: Region | null): MapFilter {
  return region
    ? ["==", ["get", "slug"], region.slug]
    : ["==", ["get", "slug"], ""];
}

function toFiniteNumber(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function extendBounds(bounds: LngLatBounds, coordinates: unknown): void {
  if (!Array.isArray(coordinates)) {
    return;
  }

  if (
    coordinates.length >= 2 &&
    toFiniteNumber(coordinates[0]) !== null &&
    toFiniteNumber(coordinates[1]) !== null
  ) {
    bounds.extend([Number(coordinates[0]), Number(coordinates[1])]);
    return;
  }

  for (const coordinate of coordinates) {
    extendBounds(bounds, coordinate);
  }
}

function fitMapToRegion(map: MapLibreMap, region: Region): void {
  const bounds = new LngLatBounds();
  extendBounds(bounds, region.geometry.coordinates);

  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, { padding: 48, duration: 700 });
  }
}

function removeLayerIfPresent(map: MapLibreMap, layerId: string): void {
  if (map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }
}

export function createRegionLayer(
  map: MapLibreMap,
  { onSelect }: RegionLayerOptions,
): RegionLayerController {
  let currentRegions: readonly Region[] = [];

  map.addSource(REGION_SOURCE_ID, {
    type: "geojson",
    data: regionsToGeoJSON([]),
  });

  map.addLayer({
    id: REGION_FILL_LAYER_ID,
    type: "fill",
    source: REGION_SOURCE_ID,
    paint: {
      "fill-color": "#2563eb",
      "fill-opacity": 0.08,
    },
  });

  map.addLayer({
    id: SELECTED_REGION_FILL_LAYER_ID,
    type: "fill",
    source: REGION_SOURCE_ID,
    filter: selectedRegionFilter(null),
    paint: {
      "fill-color": "#2563eb",
      "fill-opacity": 0.2,
    },
  });

  map.addLayer({
    id: REGION_OUTLINE_LAYER_ID,
    type: "line",
    source: REGION_SOURCE_ID,
    paint: {
      "line-color": "#2563eb",
      "line-opacity": 0.45,
      "line-width": 1.25,
    },
  });

  map.addLayer({
    id: SELECTED_REGION_OUTLINE_LAYER_ID,
    type: "line",
    source: REGION_SOURCE_ID,
    filter: selectedRegionFilter(null),
    paint: {
      "line-color": "#1d4ed8",
      "line-opacity": 0.95,
      "line-width": 2.5,
    },
  });

  const handleMouseEnter = () => {
    map.getCanvas().style.cursor = "pointer";
  };
  const handleMouseLeave = () => {
    map.getCanvas().style.cursor = "";
  };
  const handleClick = (event: MapLayerMouseEvent) => {
    const slug = event.features?.[0]?.properties?.slug;
    if (typeof slug !== "string") {
      return;
    }

    const region = currentRegions.find((candidate) => candidate.slug === slug);
    if (region) {
      onSelect(region);
    }
  };

  map.on("mouseenter", REGION_FILL_LAYER_ID, handleMouseEnter);
  map.on("mouseleave", REGION_FILL_LAYER_ID, handleMouseLeave);
  map.on("click", REGION_FILL_LAYER_ID, handleClick);

  return {
    setRegions(regions) {
      currentRegions = regions;
      const source = map.getSource(REGION_SOURCE_ID) as GeoJSONSource | undefined;
      void source?.setData(regionsToGeoJSON(regions));
    },
    setSelectedRegion(region) {
      const filter = selectedRegionFilter(region);
      map.setFilter(SELECTED_REGION_FILL_LAYER_ID, filter);
      map.setFilter(SELECTED_REGION_OUTLINE_LAYER_ID, filter);

      if (region) {
        fitMapToRegion(map, region);
      }
    },
    destroy() {
      map.off("mouseenter", REGION_FILL_LAYER_ID, handleMouseEnter);
      map.off("mouseleave", REGION_FILL_LAYER_ID, handleMouseLeave);
      map.off("click", REGION_FILL_LAYER_ID, handleClick);

      removeLayerIfPresent(map, SELECTED_REGION_OUTLINE_LAYER_ID);
      removeLayerIfPresent(map, REGION_OUTLINE_LAYER_ID);
      removeLayerIfPresent(map, SELECTED_REGION_FILL_LAYER_ID);
      removeLayerIfPresent(map, REGION_FILL_LAYER_ID);

      if (map.getSource(REGION_SOURCE_ID)) {
        map.removeSource(REGION_SOURCE_ID);
      }
    },
  };
}
