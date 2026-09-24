"use client";

import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import {
  Field,
  FieldError,
  FieldLabel,
} from "@/components/ui/field";
import type { Region } from "../types";

type RegionSelectorProps = {
  regions: Region[];
  value: Region | null;
  onValueChange: (region: Region | null) => void;
  isLoading?: boolean;
  isError?: boolean;
};

function regionLabel(region: Region) {
  return region.name;
}

export function RegionSelector({
  regions,
  value,
  onValueChange,
  isLoading = false,
  isError = false,
}: RegionSelectorProps) {
  return (
    <Field data-invalid={isError}>
      <FieldLabel htmlFor="region-selector">
        Region
      </FieldLabel>

      <Combobox
        items={regions}
        value={value}
        onValueChange={onValueChange}
        itemToStringLabel={regionLabel}
        itemToStringValue={(region) => `${region.slug}:${region.version}`}
        isItemEqualToValue={(item, selected) =>
          item.slug === selected.slug &&
          item.version === selected.version
        }
        disabled={isLoading || isError}
      >
        <ComboboxInput
          id="region-selector"
          placeholder={
            isLoading
              ? "Loading regions…"
              : "Select a region"
          }
          aria-invalid={isError}
        />

        <ComboboxContent>
          <ComboboxEmpty>No regions found.</ComboboxEmpty>

          <ComboboxList>
            {(region: Region) => (
              <ComboboxItem
                key={`${region.slug}:${region.version}`}
                value={region}
              >
                {regionLabel(region)}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>

      {isError && <FieldError>Could not load regions.</FieldError>}
    </Field>
  );
}
