# Plan: Fix Vertical Card Size on Desktop for Color Page (2024-08-02)

- [ ] **State the Problem:** Vertical cards on `app/color/[id]/page.tsx` are too tall on desktop/laptop screens.
- [ ] **Bigger Picture:** Responsive styling for large aspect-ratio content on wide viewports.
- [ ] **File Identification:** `app/color/[id]/page.tsx`.
- [ ] **Read Files:** Read the identified file to understand current card rendering.
- [ ] **Think About Solutions & Prominent Solution:**
    - Favored: Apply `max-h-[XXvh]` (e.g., `75vh`) to the vertical card's container on non-mobile screens. Image uses `object-contain`.
- [ ] **Implementation Steps:**
    - [ ] Locate JSX for front/back card image rendering in `app/color/[id]/page.tsx`.
    - [ ] Identify `isMobile` state and how card orientation (vertical/horizontal) is determined.
    - [ ] Apply conditional Tailwind classes to the image container(s):
        - When `!isMobile` and card is vertical, add `md:max-h-[75vh]` (or similar).
        - Ensure image uses `w-full h-full object-contain mx-auto` (or `w-auto h-full object-contain mx-auto` if parent strictly defines height).
    - [ ] Test with a vertical card on a desktop viewport.
- [ ] **Verification:** Confirm vertical cards are reasonably sized on desktop views on the color page. 