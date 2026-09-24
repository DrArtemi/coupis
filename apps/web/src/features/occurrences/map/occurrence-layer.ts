import {
  type GeoJSONSource,
  LngLatBounds,
  type Map as MapLibreMap,
  type MapLayerMouseEvent,
  Popup,
} from "maplibre-gl";

import { occurrencesToGeoJSON } from "../geojson";
import type { Occurrence } from "../types";
import { createOccurrencePopupContent } from "./occurrence-popup";
import {
  createUncertaintyCircle,
  EMPTY_UNCERTAINTY_GEOJSON,
} from "./uncertainty-circle";

const OCCURRENCES_SOURCE_ID = "occurrences";
const OCCURRENCES_LAYER_ID = "occurrence-points";
const UNCERTAINTY_SOURCE_ID = "occurrence-uncertainty";
const UNCERTAINTY_FILL_LAYER_ID = "occurrence-uncertainty-fill";
const UNCERTAINTY_OUTLINE_LAYER_ID = "occurrence-uncertainty-outline";

export type OccurrenceLayerController = {
  setOccurrences: (occurrences: readonly Occurrence[]) => void;
  destroy: () => void;
};

function toFiniteNumber(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = typeof value === "number" ? value : Number(value);
  return Number.isFinite(number) ? number : null;
}

function fitMapToOccurrences(
  map: MapLibreMap,
  occurrences: readonly Occurrence[],
) {
  if (occurrences.length === 1) {
    const occurrence = occurrences[0];
    if (occurrence) {
      map.easeTo({
        center: [occurrence.longitude, occurrence.latitude],
        zoom: 9,
        duration: 600,
      });
    }
    return;
  }

  if (occurrences.length > 1) {
    const bounds = new LngLatBounds();
    for (const occurrence of occurrences) {
      bounds.extend([occurrence.longitude, occurrence.latitude]);
    }

    map.fitBounds(bounds, {
      padding: 48,
      maxZoom: 10,
      duration: 600,
    });
  }
}

function removeLayerIfPresent(map: MapLibreMap, layerId: string) {
  if (map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }
}

function removeSourceIfPresent(map: MapLibreMap, sourceId: string) {
  if (map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
}

export function createOccurrenceLayer(
  map: MapLibreMap,
): OccurrenceLayerController {
  map.addSource(OCCURRENCES_SOURCE_ID, {
    type: "geojson",
    data: occurrencesToGeoJSON([]),
  });
  map.addSource(UNCERTAINTY_SOURCE_ID, {
    type: "geojson",
    data: EMPTY_UNCERTAINTY_GEOJSON,
  });
  map.addLayer({
    id: UNCERTAINTY_FILL_LAYER_ID,
    type: "fill",
    source: UNCERTAINTY_SOURCE_ID,
    paint: {
      "fill-color": "#0f766e",
      "fill-opacity": 0.14,
    },
  });
  map.addLayer({
    id: UNCERTAINTY_OUTLINE_LAYER_ID,
    type: "line",
    source: UNCERTAINTY_SOURCE_ID,
    paint: {
      "line-color": "#0f766e",
      "line-opacity": 0.65,
      "line-width": 1.5,
    },
  });
  map.addLayer({
    id: OCCURRENCES_LAYER_ID,
    type: "circle",
    source: OCCURRENCES_SOURCE_ID,
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 4, 4, 10, 7],
      "circle-color": "#0f766e",
      "circle-opacity": 0.82,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1.5,
    },
  });

  const popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    offset: 12,
  });
  const occurrenceSource = map.getSource(
    OCCURRENCES_SOURCE_ID,
  ) as GeoJSONSource;
  const uncertaintySource = map.getSource(
    UNCERTAINTY_SOURCE_ID,
  ) as GeoJSONSource;

  const clearHover = () => {
    popup.remove();
    void uncertaintySource.setData(EMPTY_UNCERTAINTY_GEOJSON);
  };

  const handleMouseEnter = (event: MapLayerMouseEvent) => {
    map.getCanvas().style.cursor = "pointer";

    const feature = event.features?.[0];
    if (!feature) {
      return;
    }

    const uncertaintyM = toFiniteNumber(feature.properties?.uncertaintyM);
    const coordinates =
      feature.geometry.type === "Point"
        ? feature.geometry.coordinates
        : null;
    const longitude = toFiniteNumber(coordinates?.[0]);
    const latitude = toFiniteNumber(coordinates?.[1]);

    void uncertaintySource.setData(
      uncertaintyM !== null && longitude !== null && latitude !== null
        ? createUncertaintyCircle(longitude, latitude, uncertaintyM)
        : EMPTY_UNCERTAINTY_GEOJSON,
    );

    popup
      .setLngLat(
        longitude !== null && latitude !== null
          ? [longitude, latitude]
          : event.lngLat,
      )
      .setDOMContent(createOccurrencePopupContent(feature.properties))
      .addTo(map);
  };

  const handleMouseLeave = () => {
    map.getCanvas().style.cursor = "";
    clearHover();
  };

  map.on("mouseenter", OCCURRENCES_LAYER_ID, handleMouseEnter);
  map.on("mouseleave", OCCURRENCES_LAYER_ID, handleMouseLeave);

  return {
    setOccurrences(occurrences) {
      clearHover();
      void occurrenceSource.setData(occurrencesToGeoJSON(occurrences));
      fitMapToOccurrences(map, occurrences);
    },
    destroy() {
      map.off("mouseenter", OCCURRENCES_LAYER_ID, handleMouseEnter);
      map.off("mouseleave", OCCURRENCES_LAYER_ID, handleMouseLeave);
      clearHover();

      removeLayerIfPresent(map, OCCURRENCES_LAYER_ID);
      removeLayerIfPresent(map, UNCERTAINTY_OUTLINE_LAYER_ID);
      removeLayerIfPresent(map, UNCERTAINTY_FILL_LAYER_ID);
      removeSourceIfPresent(map, UNCERTAINTY_SOURCE_ID);
      removeSourceIfPresent(map, OCCURRENCES_SOURCE_ID);
    },
  };
}
