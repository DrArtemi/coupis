import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { SpeciesFilters } from "./types";

export const speciesQueryKeys = {
  all: ["species"] as const,
  lists: () => [...speciesQueryKeys.all, "list"] as const,
  list: (filters: SpeciesFilters) =>
    [...speciesQueryKeys.lists(), filters] as const,
};

export function speciesQueryOptions(filters: SpeciesFilters) {
  const query = {
    ...filters,
    limit: filters.limit ?? 100,
    offset: filters.offset ?? 0,
  };

  return queryOptions({
    queryKey: speciesQueryKeys.list(query),
    queryFn: async () => {
      const { data, error, response } = await apiClient.GET(
        "/api/v1/species",
        {
          params: {
            query,
          },
        },
      );

      if (error) {
        throw new Error(`Could not load species (${response.status})`);
      }

      return data;
    },
  });
}
