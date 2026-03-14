import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sand: "#f5ecd7",
        clay: "#dd8f55",
        ink: "#15232d",
        moss: "#56725d",
        ember: "#b84431",
        mist: "#dde5df"
      },
      boxShadow: {
        glow: "0 24px 60px rgba(21, 35, 45, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
