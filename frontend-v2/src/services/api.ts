/**
 * Centralized API Base URL configuration for AVISHKAR 2.0 Frontend V2.
 * Supports VITE_API_BASE_URL environment variable for Railway/Cloud deployments,
 * falling back to relative paths for local development proxying.
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export const getApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return API_BASE_URL ? `${API_BASE_URL}${cleanEndpoint}` : cleanEndpoint;
};
