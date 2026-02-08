"use client";

import { useEffect } from "react";

export function ServiceWorkerRegister() {
  useEffect(() => {
    // TODO: Replace with Serwist when offline caching requirements are finalized.
    if (process.env.NEXT_PUBLIC_ENABLE_SW !== "true") {
      return;
    }
    if (!("serviceWorker" in navigator)) {
      return;
    }
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Fail silently in development and unsupported deployments.
    });
  }, []);

  return null;
}

