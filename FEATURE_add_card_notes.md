# Feature: Add Notes to Back of Card - Implementation Plan

This document outlines the steps to implement the feature allowing users to add notes to the back of their generated cards.

## Plan:

-   [ ] **Step 1: Database Schema Migration (New Script: `sql/02_add_card_notes_and_rename_images.sql`)**
    -   Create a new migration script `sql/02_add_card_notes_and_rename_images.sql` containing the following `ALTER TABLE` statements:
        -   `ALTER TABLE public.card_generations RENAME COLUMN horizontal_image_url TO front_horizontal_image_url;`
        -   `ALTER TABLE public.card_generations RENAME COLUMN vertical_image_url TO front_vertical_image_url;`
        -   `ALTER TABLE public.card_generations ADD COLUMN note_text TEXT DEFAULT NULL;`
        -   `ALTER TABLE public.card_generations ADD COLUMN has_note BOOLEAN DEFAULT FALSE NOT NULL;`
        -   `ALTER TABLE public.card_generations ADD COLUMN back_horizontal_image_url TEXT DEFAULT NULL;`
        -   `ALTER TABLE public.card_generations ADD COLUMN back_vertical_image_url TEXT DEFAULT NULL;`

-   [ ] **Step 2: Backend Model Update (`api/models/card_generation_models.py`)**
    -   Modify `CardGenerationRecord` Pydantic model:
        -   Change `horizontal_image_url: Optional[str]` to `front_horizontal_image_url: Optional[str] = Field(None, description="URL of the generated front horizontal card image.")`.
        -   Change `vertical_image_url: Optional[str]` to `front_vertical_image_url: Optional[str] = Field(None, description="URL of the generated front vertical card image.")`.
        -   Add `note_text: Optional[str] = Field(None, description="User's note for the back of the card.")`.
        -   Add `has_note: bool = Field(False, description="Flag indicating if a note is present.")`.
        -   Add `back_horizontal_image_url: Optional[str] = Field(None, description="URL of the generated back horizontal card image.")`.
        -   Add `back_vertical_image_url: Optional[str] = Field(None, description="URL of the generated back vertical card image.")`.
    -   Ensure `details` dictionary in `update_card_generation_status` (`api/services/supabase_service.py`) uses new `front_..._url` keys.

-   [ ] **Step 3: Backend API - New Endpoint for Saving Note (`api/routers/card_generation.py` or new file)**
    -   Create `POST /api/cards/{db_id}/add-note`.
    -   Accepts `db_id` (path) and `note_text: Optional[str]` (body).
    -   Logic: Fetch record, call back image generation (Step 4), upload images, update DB with note details and back image URLs.

-   [ ] **Step 4: Backend - Back Image Generation Service (`api/utils/card_utils.py`)**
    -   Create `async def generate_back_card_image_bytes(note_text: Optional[str], hex_color: str, orientation: str, created_at_timestamp: Optional[datetime] = None, request_id: Optional[str] = None) -> bytes:`.
    -   Background: Use a very desaturated version of `hex_color` (create helper `desaturate_hex_color`).
    -   Content: Render `note_text` or default design with creation date.

-   [ ] **Step 5: Frontend - UI for Note Input (`app/(dashboard)/page.tsx`)**
    -   In `HomePage`, after front card generation, show new UI section (textarea, "Add Note" button, "Skip" button). Manage visibility with `isNoteStepPending` state.

-   [ ] **Step 6: Frontend - Client Logic for Note Submission (`app/(dashboard)/page.tsx`)**
    -   Buttons call `POST /api/cards/{dbId}/add-note`.
    -   On success, set `isNoteStepPending=false`, redirect to `/color/[generatedExtendedId]`. Handle loading/errors.

-   [ ] **Step 7: Backend API - Update Card Retrieval (`app/api/retrieve-card-by-extended-id/[extended_id]/route.ts`)**
    -   Modify `SELECT` query to fetch `front_horizontal_image_url`, `front_vertical_image_url`, and new fields (`note_text`, `has_note`, `back_horizontal_image_url`, `back_vertical_image_url`).
    -   Update TypeScript interface (`CardDataFromDB`) in the route.

-   [ ] **Step 8: Frontend - `CardDisplay.tsx` Component Enhancement**
    -   Update props to `frontHorizontalImageUrl`, `frontVerticalImageUrl`. Add `backHorizontalImageUrl`, `backVerticalImageUrl`, `noteText`, `hasNote`, `isFlippable`.
    -   Add `isFlipped` state.
    -   If `isFlippable`, implement flip: Front face uses `front...ImageUrl`, Back face uses `back...ImageUrl`.
    -   Add "Reveal Note" button or make card clickable.

-   [ ] **Step 9: Frontend - Integrate into Color Page (`app/color/[id]/page.tsx`)**
    -   Update `CardDetails` interface.
    -   Pass new and renamed props to `CardDisplay` (e.g., `frontHorizontalImageUrl={cardDetails.frontHorizontalImageUrl}`, `isFlippable={true}`).

-   [ ] **Step 10: Testing & Refinement**
    -   Test backward compatibility for existing cards.
    -   Test full new flow (add/skip note).
    -   Verify DB, image storage, responsive design, error handling. 