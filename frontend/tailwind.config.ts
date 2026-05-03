import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201a",
        moss: "#3f5f4a",
        paper: "#f7f6ef",
        line: "#d9ded4",
        clay: "#b35b42",
        aqua: "#2e7f86"
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 32, 26, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

