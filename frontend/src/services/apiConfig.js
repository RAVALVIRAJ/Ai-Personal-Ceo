const clean = (value) => {
  if (!value) return "";
  try {
    return new URL(value.trim()).origin;
  } catch {
    return value.trim().replace(/\/+$/, "");
  }
};

export const BACKEND_API_URL = clean(import.meta.env.VITE_BACKEND_URL);
export const AI_SERVICE_API_URL = clean(import.meta.env.VITE_AI_SERVICE_URL);