/** @type {import('tailwindcss').Config} */
// "Editorial Desk" — warm-paper + ink + seal-red palette for a financial
// analysis desk. Typography pairs Chinese serif (Noto Serif SC) for headings
// with PingFang SC for body UI and JetBrains Mono for all data.
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Chinese serif for titles, strong labels, report chapters
        serif: [
          "Noto Serif SC",
          "Songti SC",
          "SimSun",
          "serif",
        ],
        // UI workhorse — keep PingFang so body readability never regresses
        sans: [
          "PingFang SC",
          "-apple-system",
          "BlinkMacSystemFont",
          "Helvetica Neue",
          "Microsoft YaHei",
          "sans-serif",
        ],
        // Data / numbers / codes / ids — always tabular, always mono
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      colors: {
        // Warm newsprint background — replaces slate-50 as page canvas
        paper: {
          DEFAULT: "#F7F4EC",
          50: "#FBFAF5",
          100: "#F7F4EC",
          200: "#EFEAD9",
          300: "#E3DAC1",
        },
        // Ink tones — replace slate-800/700/600 for primary text
        ink: {
          DEFAULT: "#1C1A18",
          900: "#1C1A18",
          800: "#2A2621",
          700: "#3F3A33",
          600: "#5A534A",
          500: "#7B7367",
          400: "#9D9588",
          300: "#C2BBAF",
          200: "#DFD9CC",
          100: "#EDE7DA",
          50: "#F5F0E4",
        },
        // Seal-red — primary brand accent, replaces blue-500 for actions
        seal: {
          DEFAULT: "#A62623",
          600: "#8B1F1C",
          500: "#A62623",
          400: "#BF3E3B",
          300: "#D76664",
          100: "#F3D9D8",
          50: "#FAEDEC",
        },
      },
      boxShadow: {
        // Subtle paper-like lift rather than generic SaaS shadow-md/lg
        paper: "0 1px 0 rgba(28,26,24,0.06), 0 2px 4px rgba(28,26,24,0.04)",
        "paper-lg": "0 1px 0 rgba(28,26,24,0.08), 0 8px 24px rgba(28,26,24,0.06)",
      },
      keyframes: {
        // Staggered fade-in for initial KPI card reveal — "printing press" feel
        printIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "print-in": "printIn 360ms cubic-bezier(0.16, 1, 0.3, 1) both",
      },
    },
  },
  plugins: [],
};
