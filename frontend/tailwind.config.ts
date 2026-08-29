import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0d1b2a",
        ivory: "#fbf7ef",
        gold: "#bb8a3d",
      },
    },
  },
  plugins: [],
} satisfies Config;

