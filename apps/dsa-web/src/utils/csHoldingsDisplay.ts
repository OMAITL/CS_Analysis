const WEAR_SUFFIX_RE = /\s*[（(][^)）]+[)）]\s*$/;

/** Strip trailing (磨损) from item name when wear is shown separately. */
export function stripWearFromItemName(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return trimmed;
  const stripped = trimmed.replace(WEAR_SUFFIX_RE, '').trim();
  return stripped || trimmed;
}

export function displayHoldingsTitle(itemName: string, wear?: string | null): string {
  const base = stripWearFromItemName(itemName);
  if (!wear?.trim()) return itemName.trim() || base;
  return base;
}

export function displayHoldingsWear(itemName: string, wear?: string | null): string | null {
  const normalized = wear?.trim();
  if (normalized) return normalized;
  const match = itemName.trim().match(WEAR_SUFFIX_RE);
  if (!match) return null;
  const inner = match[0].replace(/^[（(]|[)）]$/g, '').trim();
  return inner || null;
}
