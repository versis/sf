### 1. Goal

Modify the TIFF generation process to include a standard 5mm white passe-partout around a 130mm-wide card content area. The final output must be 300 DPI.

### 2. Current Implementation

- Individual card TIFFs are generated via the `/finalize-card-generation` endpoint, which calls `api.utils.card_utils.generate_card_image_bytes`.
- These TIFFs are generated without any passe-partout, based on fixed pixel dimensions (`CARD_WIDTH_TIFF`, `CARD_HEIGHT_TIFF`).
- A separate process for creating A4 print layouts (`api.utils.print_utils`) downloads these TIFFs and adds a passe-partout at that stage.

### 3. Problem

The current process creates inconsistencies. The passe-partout is only added during A4 layout generation, not to the individual TIFF files stored in the database. This means downloaded or individually used TIFFs will lack the desired border. It also means the A4 layout process might add a passe-partout to an image that already has one if we change the base TIFF generation.

### 4. Proposed Solution

The passe-partout will be "baked into" the TIFF file during its initial generation. This ensures that any use of the TIFF will have the correct framing. The A4 layout process will be adjusted to no longer add its own passe-partout.

This involves two main changes:
1.  **Modify `api/utils/card_utils.py`** to add the passe-partout during TIFF creation.
2.  **Modify `api/utils/print_utils.py`** to handle the new TIFFs correctly.

### 5. Implementation Plan

- [ ] **Step 1: Update Card Generation Logic (`api/utils/card_utils.py`)**
    - [ ] In `api/utils/card_utils.py`, define new constants for physical dimensions to drive the TIFF generation.
    - [ ] Modify `get_card_dimensions` to use these new constants for TIFF output, returning the pixel dimensions for the *content area*.
    - [ ] In `generate_card_image_bytes`, after the card content has been rendered, if the output is TIFF, create a new larger image with the passe-partout and paste the content onto it.
    - [ ] Ensure the rounded corners logic correctly uses the new, larger canvas dimensions.

- [ ] **Step 2: Adjust A4 Layout Generation (`api/utils/print_utils.py`)**
    - [ ] In `api/utils/print_utils.py`, modify the `A4Layout.place_card` method. The new logic should assume the incoming `card_image` is final (with passe-partout) and just needs to be placed. The existing logic that creates a passe-partout must be removed. The method should expect the incoming card's dimensions to match the layout's calculated dimensions and resize only if there is a mismatch. 