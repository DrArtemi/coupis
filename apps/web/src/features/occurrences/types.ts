import type { components, operations } from "@/generated/api-schema";

export type Occurrence = components["schemas"]["OccurrenceResponse"];
export type OccurrencePage = components["schemas"]["OccurrencePageResponse"];
export type OccurrenceFilters = NonNullable<
  operations["list_occurrences_api_v1_occurrences_get"]["parameters"]["query"]
>;
export type OccurrenceYearCount =
  components["schemas"]["OccurrenceYearCountResponse"];
export type YearRange = readonly [startYear: number, endYear: number];
