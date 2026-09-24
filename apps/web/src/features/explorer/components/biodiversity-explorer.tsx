"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ExplorerMap } from "@/features/explorer/components/explorer-map";
import { occurrencesQueryOptions } from "@/features/occurrences/queries";
import type { Occurrence } from "@/features/occurrences/types";
import { RegionSelector } from "@/features/regions/components/region-selector";
import { regionsQueryOptions } from "@/features/regions/queries";
import type { Region } from "@/features/regions/types";
import { SpeciesSelector } from "@/features/species/components/species-selector";
import { speciesQueryOptions } from "@/features/species/queries";
import type { Species } from "@/features/species/types";

const EMPTY_OCCURRENCES: Occurrence[] = [];
const EMPTY_REGIONS: Region[] = [];
const EMPTY_SPECIES: Species[] = [];

export function BiodiversityExplorer() {
  const [selectedSpecies, setSelectedSpecies] = useState<Species | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const speciesQuery = useQuery(speciesQueryOptions({ limit: 100 }));
  const regionsQuery = useQuery(regionsQueryOptions());
  const species = speciesQuery.data?.items ?? EMPTY_SPECIES;
  const regions = regionsQuery.data ?? EMPTY_REGIONS;
  const occurrenceQuery = useQuery(
    occurrencesQueryOptions({
      species_id: selectedSpecies?.id,
      region_slug: selectedRegion?.slug,
      region_version: selectedRegion?.version,
      limit: 500,
    }),
  );
  const occurrences = occurrenceQuery.data?.items ?? EMPTY_OCCURRENCES;
  const hasSelection = selectedSpecies !== null && selectedRegion !== null;

  return (
    <section className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <SpeciesSelector
          species={species}
          value={selectedSpecies}
          onValueChange={setSelectedSpecies}
          isLoading={speciesQuery.isPending}
          isError={speciesQuery.isError}
        />
        <RegionSelector
          regions={regions}
          value={selectedRegion}
          onValueChange={setSelectedRegion}
          isLoading={regionsQuery.isPending}
          isError={regionsQuery.isError}
        />
      </div>

      <div aria-live="polite" className="min-h-5 text-sm text-muted-foreground">
        {!hasSelection && (
          <p>Select a species and a region to load occurrences.</p>
        )}
        {hasSelection && occurrenceQuery.isPending && (
          <p>Loading occurrences…</p>
        )}
        {hasSelection && occurrenceQuery.isError && (
          <p role="alert" className="text-destructive">
            Could not load occurrences.
          </p>
        )}
        {hasSelection &&
          occurrenceQuery.isSuccess &&
          occurrenceQuery.data.total === 0 && (
            <p>
              No occurrences found for {selectedSpecies.scientific_name} in{" "}
              {selectedRegion.name}.
            </p>
          )}
        {hasSelection &&
          occurrenceQuery.isSuccess &&
          occurrenceQuery.data.total > 0 && (
            <p>
              Showing {occurrenceQuery.data.items.length} of{" "}
              {occurrenceQuery.data.total} occurrences for{" "}
              {selectedSpecies.scientific_name} in {selectedRegion.name}.
            </p>
          )}
      </div>

      <ExplorerMap
        occurrences={occurrences}
        regions={regions}
        selectedRegion={selectedRegion}
        onRegionSelect={setSelectedRegion}
        isLoading={hasSelection && occurrenceQuery.isFetching}
      />
    </section>
  );
}
