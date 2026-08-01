export function nok(amount: number): string {
  return amount.toLocaleString("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " kr";
}

export function money(amount: number, currency: string): string {
  if (currency === "NOK") return nok(amount);
  return amount.toLocaleString("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ` ${currency}`;
}

export function dato(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("nb-NO", { day: "2-digit", month: "2-digit", year: "numeric" });
}
