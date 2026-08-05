"use client";

import { useRouter, usePathname } from "next/navigation";

interface Tab {
  id: string;
  label: string;
}

export function SupplierTabBar({
  supplierId,
  tabs,
  activeTab,
}: {
  supplierId: string;
  tabs: Tab[];
  activeTab: string;
}) {
  const router = useRouter();
  const pathname = usePathname();

  function go(tabId: string) {
    if (tabId === "oversikt") {
      router.push(pathname);
    } else {
      router.push(`${pathname}?tab=${tabId}`);
    }
  }

  return (
    <div className="flex gap-0 border-b border-line overflow-x-auto">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => go(t.id)}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
            activeTab === t.id
              ? "border-copper text-copper"
              : "border-transparent text-muted hover:text-ink"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
