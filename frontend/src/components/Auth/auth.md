# Auth Components

Authentication-related UI helpers live here.

## Responsibilities

- Guard protected routes.
- Redirect unauthenticated users into the correct login flow.
- Keep auth UX separate from page business logic.

## Modules

- `PrivateRoute.jsx`: guards authenticated app routes and preserves the original destination for post-login redirect.

## Recent Notes

- `PrivateRoute.jsx` now waits for auth hydration before redirecting, which avoids false redirects during built-in system-token bootstrap.
