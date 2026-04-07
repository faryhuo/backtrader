# locales Directory

Internationalization resources live here.

## Responsibilities

- Store language packs under matching locale folders such as `en/` and `zh/`.
- Keep translation keys aligned across supported languages.
- Provide text-only content for `i18n.js`; business logic should stay outside locale files.

## Conventions

- Add the same key structure to every supported language when introducing a new namespace.
- Keep module names stable so pages can bind to one namespace without fallback churn.
- Use concise labels in `nav.json` and fuller explanatory copy in feature-specific files.

## Recent Notes

- Added `basis.json` for English and Chinese so the new basis arbitrage page can render bilingual content.
