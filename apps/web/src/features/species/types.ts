import type { components, operations } from "@/generated/api-schema";

export type Species = components["schemas"]["SpeciesResponse"];
export type SpeciesPage = components["schemas"]["SpeciesPageResponse"];
export type SpeciesFilters = NonNullable<operations["list_species_api_v1_species_get"]["parameters"]["query"]>;