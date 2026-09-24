"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { ExplorerMap } from "@/features/explorer/components/explorer-map";
import { SelectionSummary } from "@/features/explorer/components/selection-summary";
import { TemporalDistributionSelector } from "@/features/occurrences/components/temporal-distribution-selector";
import {
  occurrencesQueryOptions,
  occurrenceYearlyCountsQueryOptions,
} from "@/features/occurrences/queries";
import {
  clampYearRange,
  distributionToYearRange,
  fillMissingYears,
  yearRangeToApiDates,
} from "@/features/occurrences/temporal";
import type {
  Occurrence,
  YearRange,
} from "@/features/occurrences/types";
import { RegionSelector } from "@/features/regions/components/region-selector";
import { regionsQueryOptions } from "@/features/regions/queries";
import type { Region } from "@/features/regions/types";
import { SpeciesSelector } from "@/features/species/components/species-selector";
import { speciesQueryOptions } from "@/features/species/queries";
import type { Species } from "@/features/species/types";

const EMPTY_OCCURRENCES: Occurrence[] = [];
const EMPTY_REGIONS: Region[] = [];
const EMPTY_SPECIES: Species[] = [];

type ScopedYearRange = {
  selectionKey: string;
  value: YearRange;
};

export function BiodiversityExplorer() {
  const [selectedSpecies, setSelectedSpecies] = useState<Species | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [yearSelection, setYearSelection] = useState<ScopedYearRange | null>(
    null,
  );
  const speciesQuery = useQuery(speciesQueryOptions({ limit: 100 }));
  const regionsQuery = useQuery(regionsQueryOptions());
  const species = speciesQuery.data?.items ?? EMPTY_SPECIES;
  const regions = regionsQuery.data ?? EMPTY_REGIONS;
  const hasSpatialSelection =
    selectedSpecies !== null && selectedRegion !== null;
  const selectionKey = hasSpatialSelection
    ? `${selectedSpecies.id}:${selectedRegion.slug}:${selectedRegion.version}`
    : null;
  const yearlyCountsQuery = useQuery(
    occurrenceYearlyCountsQueryOptions({
      speciesId: selectedSpecies?.id ?? null,
      regionSlug: selectedRegion?.slug ?? null,
      regionVersion: selectedRegion?.version ?? null,
    }),
  );
  const yearlyDistribution = useMemo(
    () => fillMissingYears(yearlyCountsQuery.data?.items ?? []),
    [yearlyCountsQuery.data],
  );
  const availableYears = useMemo(
    () => distributionToYearRange(yearlyDistribution),
    [yearlyDistribution],
  );
  const selectedYears = useMemo(() => {
    if (!availableYears || !selectionKey) {
      return null;
    }
    return yearSelection?.selectionKey === selectionKey
      ? clampYearRange(yearSelection.value, availableYears)
      : availableYears;
  }, [availableYears, selectionKey, yearSelection]);
  const apiDates = selectedYears
    ? yearRangeToApiDates(selectedYears)
    : null;
  const occurrenceQuery = useQuery(
    occurrencesQueryOptions({
      species_id: selectedYears ? selectedSpecies?.id : undefined,
      region_slug: selectedRegion?.slug,
      region_version: selectedRegion?.version,
      observed_from: apiDates?.observedFrom,
      observed_until: apiDates?.observedUntil,
      limit: 500,
    }),
  );
  const occurrences = occurrenceQuery.data?.items ?? EMPTY_OCCURRENCES;
  const occurrenceCount =
    occurrenceQuery.data?.total ??
    (hasSpatialSelection &&
    yearlyCountsQuery.isSuccess &&
    availableYears === null
      ? 0
      : null);

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

      <TemporalDistributionSelector
        key={`${selectionKey ?? "none"}:${availableYears?.join(":") ?? "pending"}`}
        distribution={yearlyDistribution}
        availableRange={availableYears}
        value={selectedYears}
        onValueChange={(value) => {
          if (selectionKey) {
            setYearSelection({ selectionKey, value });
          }
        }}
        enabled={hasSpatialSelection}
        isLoading={hasSpatialSelection && yearlyCountsQuery.isPending}
        isError={yearlyCountsQuery.isError}
      />

      <SelectionSummary
        species={selectedSpecies}
        region={selectedRegion}
        years={selectedYears}
        occurrenceCount={occurrenceCount}
        isLoading={occurrenceQuery.isFetching}
      />

      <div aria-live="polite" className="min-h-5 text-sm text-muted-foreground">
        {selectedYears && occurrenceQuery.isError && (
          <p role="alert" className="text-destructive">
            Could not load occurrences.
          </p>
        )}
        {hasSpatialSelection &&
          selectedYears &&
          occurrenceQuery.isSuccess &&
          occurrenceQuery.data.total === 0 && (
            <p>
              No occurrences found for {selectedSpecies.scientific_name} in{" "}
              {selectedRegion.name}.
            </p>
          )}
        {selectedYears &&
          occurrenceQuery.isSuccess &&
          occurrenceQuery.data.total > occurrenceQuery.data.items.length && (
            <p>
              The map shows the first {occurrenceQuery.data.items.length} of{" "}
              {occurrenceQuery.data.total} matching observations.
            </p>
          )}
      </div>

      <ExplorerMap
        occurrences={occurrences}
        regions={regions}
        selectedRegion={selectedRegion}
        onRegionSelect={setSelectedRegion}
        isLoading={selectedYears !== null && occurrenceQuery.isFetching}
      />
    </section>
  );
}
