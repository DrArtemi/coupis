import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

import type { OccurrenceFilters } from "./types";

export const occurrenceQueryKeys = {
  all: ["occurrences"] as const,
  lists: () => [...occurrenceQueryKeys.all, "list"] as const,
  list: (filters: OccurrenceFilters) =>
    [...occurrenceQueryKeys.lists(), filters] as const,
};

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
