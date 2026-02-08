import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        msc: {
          navy: "var(--msc-navy)",
          burgundy: "var(--msc-burgundy)",
          slate: "var(--msc-slate)",
          bg: "var(--msc-bg)",
          card: "var(--msc-card)",
          muted: "var(--msc-muted)",
        },
      },
    },
  },
  plugins: [],
};

export default config;
