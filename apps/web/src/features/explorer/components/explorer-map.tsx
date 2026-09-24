"use client";

import { useEffect, useRef } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
} from "maplibre-gl";

import {
  createOccurrenceLayer,
  type OccurrenceLayerController,
} from "@/features/occurrences/map/occurrence-layer";
import type { Occurrence } from "@/features/occurrences/types";
import {
  createRegionLayer,
  type RegionLayerController,
} from "@/features/regions/map/region-layer";
import type { Region } from "@/features/regions/types";

const DEFAULT_CENTER: [number, number] = [5, 46.5];
const DEFAULT_ZOOM = 4.5;

setWorkerUrl("/maplibre-gl-csp-worker.js");

type ExplorerMapProps = {
  occurrences: readonly Occurrence[];
  regions: readonly Region[];
  selectedRegion: Region | null;
  onRegionSelect: (region: Region) => void;
  isLoading?: boolean;
};

export function ExplorerMap({
  occurrences,
  regions,
  selectedRegion,
  onRegionSelect,
  isLoading = false,
}: ExplorerMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const occurrenceLayerRef = useRef<OccurrenceLayerController | null>(null);
  const regionLayerRef = useRef<RegionLayerController | null>(null);
  const occurrencesRef = useRef(occurrences);
  const regionsRef = useRef(regions);
  const selectedRegionRef = useRef(selectedRegion);
  const onRegionSelectRef = useRef(onRegionSelect);

  useEffect(() => {
    onRegionSelectRef.current = onRegionSelect;
  }, [onRegionSelect]);

  useEffect(() => {
    regionsRef.current = regions;
    regionLayerRef.current?.setRegions(regions);
  }, [regions]);

  useEffect(() => {
    selectedRegionRef.current = selectedRegion;
    regionLayerRef.current?.setSelectedRegion(selectedRegion);
  }, [selectedRegion]);

  useEffect(() => {
    occurrencesRef.current = occurrences;
    occurrenceLayerRef.current?.setOccurrences(occurrences);
  }, [occurrences]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = new MapLibreMap({
      container: containerRef.current,
      style: "https://tiles.openfreemap.org/styles/positron",
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
    });
    map.addControl(new NavigationControl(), "top-right");
    mapRef.current = map;

    const handleLoad = () => {
      const regionLayer = createRegionLayer(map, {
        onSelect: (region) => onRegionSelectRef.current(region),
      });
      const occurrenceLayer = createOccurrenceLayer(map);

      regionLayerRef.current = regionLayer;
      occurrenceLayerRef.current = occurrenceLayer;

      regionLayer.setRegions(regionsRef.current);
      regionLayer.setSelectedRegion(selectedRegionRef.current);
      occurrenceLayer.setOccurrences(occurrencesRef.current);
    };

    map.once("load", handleLoad);

    return () => {
      map.off("load", handleLoad);
      occurrenceLayerRef.current?.destroy();
      regionLayerRef.current?.destroy();
      occurrenceLayerRef.current = null;
      regionLayerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <div className="relative overflow-hidden rounded-xl border bg-muted">
      <div
        ref={containerRef}
        className="h-[32rem] w-full"
        aria-label="Map of biodiversity occurrences"
      />
      {isLoading && (
        <div className="pointer-events-none absolute left-3 top-3 rounded-md bg-background/90 px-3 py-2 text-sm shadow-sm">
          Updating occurrences…
        </div>
      )}
    </div>
  );
}
