import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "MSC Super Friend",
    short_name: "MSC Friend",
    description: "Mobile-first interface for doctrine, toolkit resources, and Ask Super Friend.",
    start_url: "/",
    display: "standalone",
    background_color: "#f2f4f6",
    theme_color: "#0b3c5d",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}

