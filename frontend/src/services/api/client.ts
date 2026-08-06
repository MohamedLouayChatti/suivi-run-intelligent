import axios, { type AxiosError } from "axios";

import { getAuthToken, notifyAuthFailure } from "@/lib/auth";

import { normalizeApiError, type BackendErrorBody } from "./errors";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

if (!process.env.NEXT_PUBLIC_API_BASE_URL && process.env.NODE_ENV !== "production") {
  console.warn(
    `NEXT_PUBLIC_API_BASE_URL is not set — falling back to ${API_BASE_URL}. Set it in .env.local.`,
  );
}

/**
 * The single Axios instance for the whole app. Feature API modules under
 * src/services/api/* import this instead of configuring HTTP themselves —
 * base URL, JWT attachment, and error normalization all live here, once.
 *
 * No default Content-Type header: axios's own transformRequest already sets
 * `application/json` for plain object bodies. A blanket default here would
 * make axios see `hasJSONContentType` as true for FormData bodies too, and
 * JSON-stringify the FormData wrapper instead of sending real multipart
 * bytes — breaking every file upload silently (server sees a body with no
 * `file` field and 422s).
 */
const httpClient = axios.create({
  baseURL: API_BASE_URL,
});

httpClient.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<BackendErrorBody>) => {
    if (error.response?.status === 401) {
      notifyAuthFailure();
    }
    return Promise.reject(normalizeApiError(error));
  },
);

export { httpClient, API_BASE_URL };
