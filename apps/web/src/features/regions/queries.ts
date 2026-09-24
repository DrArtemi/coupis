import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export const regionQueryKeys = {
  all: ["regions"] as const,
};

export function regionsQueryOptions() {
  return queryOptions({
    queryKey: regionQueryKeys.all,
    queryFn: async () => {
      const { data, error, response } = await apiClient.GET(
        "/api/v1/regions",
      );

      if (error) {
        throw new Error(`Could not load regions (${response.status})`);
      }
      return data;
    },
  });
}
