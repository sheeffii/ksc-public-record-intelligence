import { defineConfig, globalIgnores } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextCoreWebVitals,
  ...nextTypescript,
  globalIgnores([".next/**", "out/**", "coverage/**", "next-env.d.ts"]),
  {
    rules: {
      // Interface strings come from the string table (HANDOFF.md §10.5).
      // This rule is the mechanical half of that policy; the review half is
      // the components themselves.
      "react/jsx-no-literals": "off",
    },
  },
]);
