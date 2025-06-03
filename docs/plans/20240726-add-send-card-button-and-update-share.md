# Plan: Add "Send The Card" Button and Update Share Functionality on Color Page

Date: 2024-07-26

## Problem Statement
The user wants to:
1. Add a new "Send The Card" button on the `app/color/[id]/ClientCardPage.tsx`. This button should replicate the functionality of the current "Share" button and be placed between the "Reveal Card Back" and "More Options" buttons.
2. Remove the "Share" option from the "More Options" dropdown menu.
3. List the feedback messages displayed to the user after a successful send or copy action.

## Affected Files
- `app/color/[id]/ClientCardPage.tsx` (primary, via `CardDisplay.tsx`)
- `components/CardDisplay.tsx` (modified directly)
- `lib/shareUtils.ts` (for understanding messages)
- `app/(dashboard)/page.tsx` (for reference on `handleShare` and messages)
- `lib/constants.ts` (to get `COPY_SUCCESS_MESSAGE`)

## Implementation Steps

- [x] **Step 1: Read `app/color/[id]/ClientCardPage.tsx`, `lib/shareUtils.ts`, `components/CardDisplay.tsx`, and `lib/constants.ts`**
    - [x] Understand how `handleShare` (or equivalent) is implemented in `ClientCardPage.tsx`.
    - [x] Identify where the "More Options" dropdown items are defined in `CardDisplay.tsx`.
    - [x] Identify the success/error messages used by `shareOrCopy` from `lib/shareUtils.ts` or its usage, and `COPY_SUCCESS_MESSAGE` from `lib/constants.ts`.
- [x] **Step 2: Implement "Send The Card" Button in `components/CardDisplay.tsx`**
    - [x] Import `Mail` icon from `lucide-react`.
    - [x] Add a new `<button>` element.
    - [x] Position it between "Reveal Card Back" and "More Options" buttons.
    - [x] Apply styling consistent with existing action buttons (new blue style defined).
    - [x] Ensure it calls the `handleShare` prop.
- [x] **Step 3: Remove "Share" from Dropdown in `components/CardDisplay.tsx`**
    - [x] Locate the definition of the dropdown menu items.
    - [x] Remove or filter out the "Share" option.
- [x] **Step 4: List User Feedback Messages**
    - [x] Document the exact messages for share success, copy success, share error, and copy error based on the implementation.
- [x] **Step 5: Final Review**
    - [x] Mentally review the changes to ensure all requirements are met. 