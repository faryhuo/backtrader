# Layout Directory

Global application layout and navigation components live here.

## Components

- `Layout.jsx`: application shell that wraps the sidebar, header region, and routed content.
- `Menu.jsx`: sidebar navigation with route highlighting, collapse behavior, and auth-aware entries.
- `NotificationCenter.jsx`: shared notification surface for app-level feedback.

## Responsibilities

- Keep layout and navigation concerns separate from page business logic.
- Maintain route discoverability and consistent grouping in the sidebar.
- Preserve responsive behavior across desktop and smaller viewports.

## Conventions

- Add new sidebar destinations only when a matching route exists in `frontend/src/App.jsx`.
- Prefer translation keys for visible labels so collapsed titles and full labels stay aligned.
- Keep access control decisions in the menu limited to visibility logic, not feature execution.

## Recent Notes

- `Menu.jsx` now includes a dedicated `Basis Arbitrage` entry under the strategy and trading group.
