# Plan: Replace Hardcoded Site URL with Environment Variable

Date: 2024-07-28

## Goal

Replace hardcoded instances of `https://sf.tinker.institute/` with the environment variable `NEXT_PUBLIC_API_URL`.

## Steps

- [x] 1. **Identify Occurrences**: Searched codebase for `https://sf.tinker.institute/`.
    - Found in:
        - `app/layout.tsx`
        - `app/(dashboard)/page.tsx`
        - `app/color/[id]/ClientCardPage.tsx`
        - `app/color/[id]/page.tsx` (discovered in follow-up)
- [x] 2. **Modify `app/layout.tsx`**:
    - Replaced hardcoded URLs with `process.env.NEXT_PUBLIC_API_URL`. Removed fallback URL.
- [x] 3. **Modify `app/(dashboard)/page.tsx`**:
    - Replaced hardcoded URLs with `process.env.NEXT_PUBLIC_API_URL`. Removed fallback URL.
- [x] 4. **Modify `app/color/[id]/ClientCardPage.tsx`**:
    - Replaced hardcoded URL with `process.env.NEXT_PUBLIC_API_URL`. Removed fallback URL.
- [x] 5. **Modify `app/color/[id]/page.tsx`**:
    - Replaced hardcoded URLs in `fetchCardData` and `generateMetadata` with `process.env.NEXT_PUBLIC_API_URL`.
- [x] 6. **Documentation & Setup**:
    - Advised user to add `NEXT_PUBLIC_API_URL=https://sf.tinker.institute` to their `.env.local` file for local development.
    - Ensured code relies solely on the environment variable, using non-null assertions (`!`) where appropriate to fail fast if the variable is not set.

## Notes
- The environment variable `NEXT_PUBLIC_API_URL` should end *without* a trailing slash for consistency (e.g., `NEXT_PUBLIC_API_URL=https://sf.tinker.institute`). The code handles adding trailing slashes where necessary.
- It is crucial that `NEXT_PUBLIC_API_URL` is defined in all environments, as the application now strictly depends on it. 