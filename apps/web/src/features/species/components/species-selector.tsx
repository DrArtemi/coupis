"use client";

import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import type { Species } from "../types";

type SpeciesSelectorProps = {
  species: Species[];
  value: Species | null;
  onValueChange: (species: Species | null) => void;
  isLoading?: boolean;
  isError?: boolean;
};

function speciesLabel(species: Species) {
  return species.scientific_name;
}

export function SpeciesSelector({
  species,
  value,
  onValueChange,
  isLoading = false,
  isError = false,
}: SpeciesSelectorProps) {
  return (
    <Field data-invalid={isError}>
      <FieldLabel htmlFor="species-selector">Species</FieldLabel>

      <Combobox
        items={species}
        value={value}
        onValueChange={onValueChange}
        itemToStringLabel={speciesLabel}
        itemToStringValue={speciesLabel}
        isItemEqualToValue={(item, selected) => item.id === selected.id}
        disabled={isLoading || isError}
      >
        <ComboboxInput
          id="species-selector"
          placeholder={isLoading ? "Loading species…" : "Select a species"}
          aria-invalid={isError}
        />

        <ComboboxContent>
          <ComboboxEmpty>No species found.</ComboboxEmpty>

          <ComboboxList>
            {(species: Species) => (
              <ComboboxItem key={species.id} value={species}>
                {speciesLabel(species)}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>

      {isError && <FieldError>Could not load species.</FieldError>}
    </Field>
  );
}
