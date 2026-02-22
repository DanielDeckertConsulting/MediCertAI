/**
 * Centralized auth redirect URIs for web vs native (Capacitor).
 * In Capacitor, B2C must use capacitor://localhost/auth/callback.
 */

declare global {
  interface Window {
    Capacitor?: { isNativePlatform?: () => boolean };
  }
}

function isCapacitor(): boolean {
  return typeof window !== "undefined" && Boolean(window.Capacitor?.isNativePlatform?.());
}

/** Redirect URI for OIDC/B2C login. Use in auth init. */
export function getAuthRedirectUri(): string {
  const env = import.meta.env.VITE_AUTH_REDIRECT_URI;
  if (env) return env;
  if (isCapacitor()) return "capacitor://localhost/auth/callback";
  if (typeof window !== "undefined") return `${window.location.origin}/auth/callback`;
  return "/auth/callback";
}

/** Post-logout redirect (optional). */
export function getAuthPostLogoutRedirectUri(): string {
  const env = import.meta.env.VITE_AUTH_POST_LOGOUT_REDIRECT_URI;
  if (env) return env;
  if (isCapacitor()) return "capacitor://localhost";
  if (typeof window !== "undefined") return window.location.origin;
  return "/";
}
