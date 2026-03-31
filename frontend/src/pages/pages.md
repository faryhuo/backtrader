# pages Directory

Route-level React pages live here. Pages assemble feature components, page-level data loading, and navigation flow.

## Responsibilities

- Own top-level route composition.
- Keep business logic delegated to hooks, services, and feature components.
- Handle page loading, error, and empty states.
- Coordinate auth redirects with `App.jsx` and `components/Auth/`.

## Key Pages

- `Home.jsx`: landing page and marketing entry.
- `Login.jsx`: unified login page for built-in system auth and Logto entry.
- `Callback.jsx`: Logto OAuth callback.
- `Settings.jsx`: runtime configuration page, including auth provider settings.
- `OnboardingSetup.jsx`: first-run setup wizard.

## Conventions

- Add new routes in `frontend/src/App.jsx`.
- Prefer service-layer API calls instead of raw `fetch` inside pages.
- Keep page files focused on layout and flow control.

## Recent Notes

- `Login.jsx` now provides built-in email/password login and optional registration when the backend is configured for `system` auth.
- `App.jsx` now routes authentication through a provider-based flow so `logto` and `system` login can share the same guarded app shell.
- `OnboardingSetup.jsx` now supports system-auth bootstrap fields for the first administrator and avoids forcing those fields once system users already exist.
- `OnboardingSetup.jsx` now persists the bootstrap system-auth token returned after first-run admin creation and reloads into the authenticated app shell instead of re-querying the setup wizard anonymously.
- `Settings.jsx` now exposes built-in system-user management for authenticated system admins.
