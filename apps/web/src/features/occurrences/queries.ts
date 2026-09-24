import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

import type { OccurrenceFilters } from "./types";

export const occurrenceQueryKeys = {
  all: ["occurrences"] as const,
  lists: () => [...occurrenceQueryKeys.all, "list"] as const,
  list: (filters: OccurrenceFilters) =>
    [...occurrenceQueryKeys.lists(), filters] as const,
  yearlyCounts: (filters: OccurrenceSelectionFilters) =>
    [...occurrenceQueryKeys.all, "yearly-counts", filters] as const,
};

type OccurrenceSelectionFilters = {
  speciesId: number | null;
  regionSlug: string | null;
  regionVersion: number | null;
};

export function occurrenceYearlyCountsQueryOptions(
  filters: OccurrenceSelectionFilters,
) {
  const enabled = filters.speciesId !== null && filters.regionSlug !== null;

  return queryOptions({
    queryKey: occurrenceQueryKeys.yearlyCounts(filters),
    enabled,
    queryFn: async () => {
      if (filters.speciesId === null || filters.regionSlug === null) {
        throw new Error("Species and region are required");
      }

      const { data, error, response } = await apiClient.GET(
        "/api/v1/occurrences/yearly-counts",
        {
          params: {
            query: {
              species_id: filters.speciesId,
              region_slug: filters.regionSlug,
              region_version: filters.regionVersion,
            },
          },
        },
      );

      if (error) {
        throw new Error(
          `Could not load yearly occurrence counts (${response.status})`,
        );
      }

      return data;
    },
    staleTime: 30_000,
  });
}

export function occurrencesQueryOptions(filters: OccurrenceFilters) {
  const query = {
    ...filters,
    limit: filters.limit ?? 100,
    offset: filters.offset ?? 0,
  };
  const enabled = query.species_id != null && query.region_slug != null;

  return queryOptions({
    queryKey: occurrenceQueryKeys.list(query),
    enabled,
    queryFn: async () => {
      const { data, error, response } = await apiClient.GET(
        "/api/v1/occurrences",
        {
          params: {
            query,
          },
        },
      );

      if (error) {
        throw new Error(`Could not load occurrences (${response.status})`);
      }

      return data;
    },
    staleTime: 30_000,
  });
}
