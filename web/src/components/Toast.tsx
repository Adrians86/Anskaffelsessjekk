"use client";

import { useEffect, useState } from "react";

export function Toast({
  message,
  type = "success",
  onDismiss,
}: {
  message: string;
  type?: "success" | "error";
  onDismiss: () => void;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // mount with delay to trigger CSS transition
    const t1 = setTimeout(() => setVisible(true), 10);
    const t2 = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 3000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDismiss]);

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg text-sm font-medium transition-all duration-300 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
      } ${
        type === "success"
          ? "bg-samsvar-bg text-samsvar border-samsvar/30"
          : "bg-avvik-bg text-avvik border-avvik/30"
      }`}
    >
      <span>{type === "success" ? "✓" : "✗"}</span>
      <span>{message}</span>
      <button onClick={() => { setVisible(false); setTimeout(onDismiss, 300); }} className="ml-2 opacity-60 hover:opacity-100">×</button>
    </div>
  );
}

export function useToast() {
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  function showToast(message: string, type: "success" | "error" = "success") {
    setToast({ message, type });
  }

  function ToastNode() {
    if (!toast) return null;
    return <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />;
  }

  return { showToast, ToastNode };
}
