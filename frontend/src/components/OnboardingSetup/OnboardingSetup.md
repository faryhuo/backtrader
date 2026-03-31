# OnboardingSetup Directory

This directory contains reusable sections used by the first-run onboarding wizard.

## Responsibilities

- Keep large onboarding step UIs out of `OnboardingSetup.jsx`.
- Accept page-owned state and callbacks through props.
- Encapsulate step-specific presentation while leaving cross-step validation in the page layer.

## Current Components

- `SettingRow.jsx`: shared label, help text, and content layout wrapper.
- `DataSourceSetupSection.jsx`: data-source toggles, priority ordering, and EODHD key entry.
- `AISetupSection.jsx`: AI provider configuration and connection testing.
- `TradingSetupSection.jsx`: Binance paper/live credentials, guidance, and test actions.
- `ReviewSummary.jsx`: final review of effective onboarding overrides.

## Conventions

- Keep component interfaces explicit and prop-driven.
- Reuse `OnboardingSetup.css` styles before introducing new variants.
- Preserve the existing wizard step order and rely on the page for navigation and validation.

## Recent Notes

- System auth onboarding now supports first-admin bootstrap fields so a locked-down public deployment can create its initial administrator during setup.
- Review output remains diff-driven; avoid hard-coding a separate summary model for each onboarding field.
