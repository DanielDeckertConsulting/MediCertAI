# MentalCarePilot — Mobile app (PWA + Capacitor)

This document describes how to build and run the MentalCarePilot web app as a **PWA** (installable on mobile/desktop) and as **native iOS/Android** apps via Capacitor.

## Prerequisites

- **Node.js** ≥ 20, **pnpm** 9.x
- **Android:** Android Studio (for building/running the Android app)
- **iOS:** Xcode on macOS (for building/running the iOS app)
- **Web/PWA:** Modern browser (Chrome, Safari, Edge)

## Running the web app (dev)

```bash
pnpm run dev
# or
pnpm run dev:web
```

- App: http://localhost:5173
- API proxy: `/api` → backend (e.g. http://localhost:8000)

## Building for production

```bash
pnpm run build
```

- Output: `apps/web/dist/`
- The build includes PWA manifest and service worker (auto-update).

## PWA (installable web app)

1. Build: `pnpm run build`
2. Preview the built PWA locally: `pnpm run pwa:preview` (serves `apps/web/dist` for testing install)
3. In production, deploy `apps/web/dist` to your host (HTTPS required for install).
4. In supported browsers (Chrome Android, desktop Chrome, Edge), use “Install” / “Add to Home Screen”.

**Behavior:**

- **Install:** Manifest + service worker make the app installable.
- **Updates:** Service worker uses `autoUpdate`; a new deployment is picked up on next load.
- **Caching:** Only app shell/assets are cached; **API and streaming endpoints are not cached** so chat streaming works as expected.

## Android (Capacitor)

1. Build web assets and sync to native project:
   ```bash
   pnpm run cap:sync
   ```
2. Open Android Studio and run:
   ```bash
   pnpm run android
   ```
   Or open `android/` in Android Studio and run the app.

- Web content is loaded from `apps/web/dist` (copied into `android/app/src/main/assets/public` by `cap sync`).

## iOS (Capacitor)

1. Build and sync:
   ```bash
   pnpm run cap:sync
   ```
2. Open Xcode and run:
   ```bash
   pnpm run ios
   ```
   Or open `ios/App/App.xcworkspace` in Xcode and run on simulator or device.

- **Note:** iOS build requires macOS and Xcode. If you don’t have a Mac, the iOS project is still committed; you can build it when a Mac is available.

## Auth redirect URIs (Azure B2C / OIDC)

The app supports both **web** and **native (Capacitor)** redirects.

### Environment variables

- **`VITE_AUTH_REDIRECT_URI`** — Redirect URI after login (optional; see below).
- **`VITE_AUTH_POST_LOGOUT_REDIRECT_URI`** — Redirect after logout (optional).

If unset:

- **Web:** Redirect URI is `${origin}/auth/callback` (e.g. `https://your-domain.com/auth/callback`).
- **Capacitor (native):** Redirect URI is `capacitor://localhost/auth/callback`.

### Callback route

- The app has a stable callback route: **`/auth/callback`**.
- After B2C/OIDC redirect, the user lands on this route; the app then processes the token/code and redirects to the main app (e.g. `/`).

### Azure B2C app registration

In your Azure B2C app registration, add the following **Redirect URIs**:

- **Web (production):** `https://<your-domain>/auth/callback`
- **Web (local dev):** `http://localhost:5173/auth/callback`
- **Capacitor (native):** `capacitor://localhost/auth/callback`

For **post-logout** redirect (optional):

- Web: `https://<your-domain>` or `http://localhost:5173`
- Native: `capacitor://localhost`

### Future hardening (not in MVP)

- **iOS:** Configure **Universal Links** so `https://<domain>/auth/callback` opens the app.
- **Android:** Configure **App Links** for the same.

## Known limitations (MVP)

- **No offline chat** — Requires network.
- **No push notifications** — Can be added later.
- **No biometric auth** — Can be added later.
- PWA icons are placeholder SVGs; replace with brand PNGs (192×192, 512×512) for full Lighthouse PWA score if desired.

## Scripts summary

| Script         | Description                                  |
|----------------|----------------------------------------------|
| `pnpm run dev` | Run web app (Vite dev server)                |
| `pnpm run build` | Build web app → `apps/web/dist`           |
| `pnpm run pwa:preview` | Build + serve dist for PWA testing   |
| `pnpm run cap:sync` | Build + `cap sync` (copy dist into native projects) |
| `pnpm run android` | Open Android project in Android Studio   |
| `pnpm run ios` | Open iOS project in Xcode                   |

## Verification checklist (for PR / release)

- [ ] `pnpm run build` successful
- [ ] PWA installable in Chrome (Android) and desktop Chrome
- [ ] Service worker registered, updates auto
- [ ] Chat streaming works (no SW caching issue)
- [ ] Capacitor Android project builds
- [ ] iOS project generated (build best-effort)
- [ ] Auth callback route works (web + capacitor scheme)
- [ ] 390px mobile sanity check passed (no horizontal scroll; input not blocked)
