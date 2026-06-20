import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en", "es", "fr", "de", "hi", "ja", "zh"],
  defaultLocale: "en",
  localePrefix: "as-needed",
});
