import createClient from "openapi-fetch";

import type { paths } from "@/generated/api-schema";

const baseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export const apiClient = createClient<paths>({ baseUrl });
