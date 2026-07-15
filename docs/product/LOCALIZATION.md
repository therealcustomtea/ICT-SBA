# Localization

Cipherboard launches in English (`en`) and Traditional Chinese (`zh-Hant`). Routes carry the locale prefix, while game colour IDs, modes, status values, error codes, database records, and analytics properties stay language-independent.

## Catalog rules

Translation catalogs live in `apps/web/messages`. Keys are stable product contracts: reuse an existing key for the same meaning, add a new descriptive key for new meaning, and do not assemble sentences from translated fragments. Keep interpolation variables, plurals, punctuation intent, and accessible names equivalent across locales.

Dates and numbers use locale-aware platform formatters. User-authored names and challenge titles are normalized but never translated. Legal copy must receive legal review in every launch locale.

## Adding a locale

1. Add the locale to `apps/web/i18n/routing.ts` and create a complete catalog from the English key set.
2. Add localized colour names, rules, errors, game states, sharing copy, statistics, achievements, account controls, administrative labels, and legal navigation.
3. Extend locale tests so scalar key paths and interpolation variables match every existing catalog.
4. Add route-level Playwright coverage for navigation, gameplay, metadata, private-page no-index behavior, and a mobile viewport.
5. Review line wrapping, input methods, plural behavior, screen-reader pronunciation, date/number formatting, and 200%/400% zoom with a fluent reviewer.
6. Update public language selection and this document only after the catalog and review are complete.

Do not ship a partially translated primary flow or silently fall back inside a translated sentence.
