export function formatIQ(v?: number | null): string {
  return Number.isFinite(v as number) ? (v as number).toFixed(2) : 'N/A';
}
