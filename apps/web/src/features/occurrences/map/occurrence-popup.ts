function appendPopupDetail(
  list: HTMLDListElement,
  label: string,
  value: unknown,
) {
  if (value === null || value === undefined || value === "") {
    return;
  }

  const row = document.createElement("div");
  row.className = "grid grid-cols-[auto_1fr] gap-x-2";

  const term = document.createElement("dt");
  term.className = "font-medium text-muted-foreground";
  term.textContent = label;

  const description = document.createElement("dd");
  description.className = "text-foreground";
  description.textContent = String(value);

  row.append(term, description);
  list.append(row);
}

export function createOccurrencePopupContent(
  properties: Record<string, unknown> | null,
) {
  const content = document.createElement("div");
  content.className = "min-w-52 space-y-2 text-sm";

  const title = document.createElement("p");
  title.className = "font-semibold text-foreground";
  title.textContent = "Occurrence";

  const details = document.createElement("dl");
  details.className = "space-y-1";

  appendPopupDetail(details, "GBIF ID", properties?.gbifId);
  appendPopupDetail(details, "Record type", properties?.basisOfRecord);
  appendPopupDetail(details, "Observed", properties?.observedAt);
  appendPopupDetail(details, "Locality", properties?.locality);

  const uncertainty = properties?.uncertaintyM;
  appendPopupDetail(
    details,
    "Uncertainty",
    typeof uncertainty === "number" ? `${uncertainty} m` : uncertainty,
  );

  content.append(title, details);
  return content;
}
