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
 */
const httpClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
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

export { httpClient };
