# Plan: Replace "card" with "postcard" in User-Visible Text

Date: 2024-07-26

## Goal
Identify all user-visible occurrences of the word "card" (and its variations like "Card", "cards") in the application's pages and replace them with "postcard" (or "Postcard", "postcards") where appropriate.

## Steps

- [x] **Step 1: Create a Plan Document.** (Done)
- [x] **Step 2: Identify Potential Files.**
    - [x] List files in `app/` directory (attempted, used project layout due to timeouts).
- [x] **Step 3: Search for "card" Occurrences.**
    - [x] Perform a case-insensitive search for "card" in relevant files (`.tsx` in `app/` and `components/`).
- [x] **Step 4: Analyze and Replace.**
    - [x] For each identified file and occurrence:
        - [x] Read file content (some files read successfully, `app/(dashboard)/page.tsx` timed out).
        - [x] Determine if the text is user-visible.
        - [x] If yes, propose `edit_file` to change "card" to "postcard".
- [ ] **Step 5: Review.**
    - [ ] Manually review all changes.
    - [ ] (Optional) Run the application to visually inspect changes.

## Files Checked & Status:

- `components/CardDisplay.tsx`: **Modified** (alt texts, user message, button title)
- `components/ImageCardDisplay.tsx`: **Modified** (comment, user text, alt text, aria-labels)
- `app/(dashboard)/review/page.tsx`: **Modified** (user-visible labels, link text, comment)
- `app/color/[id]/page.tsx`: **Modified** (comments, log messages, metadata, fallback text)
- `components/ColorTools.tsx`: **Modified** (comments related to layout)
- `app/(dashboard)/page.tsx`: **Skipped** (Edits to comments and console logs failed due to tool errors/timeouts reading and applying changes)
- `components/WizardStep.tsx`: **Skipped** (Contained CSS class names like `bg-card`, not user text)
- `app/layout.tsx`: **Skipped** (Contained metadata `card: "summary_large_image"`, not user text)


## Notes:
- Be careful not to change internal identifiers (e.g., `cardId`, `CardComponent`).
- Handle variations: "card", "Card", "cards", "Cards".
- API endpoints (e.g., `/api/batch-retrieve-cards`) and internal variable/property names (e.g., `card`, `batchResult.cards`) were generally not changed unless they directly produced user-visible text or were trivial to update for consistency (like simple log messages).
- Edits to `app/(dashboard)/page.tsx` could not be completed due to persistent tool issues. 