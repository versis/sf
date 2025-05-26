# Plan for Updating Card Icons

- [x] **State the problem**: Rephrased the user's request to ensure understanding.
- [x] **Identify relevant files**: Searched for files related to card design and icons. (`api/utils/card_utils.py`, `components/CardDisplay.tsx`)
- [x] **Read relevant files**: Understood the current implementation in `api/utils/card_utils.py`.
- [ ] **Propose solutions**:
    - [x] Solution 1: Directly replace the existing icon rendering logic with PIL image pasting in `api/utils/card_utils.py`.
    - [ ] Solution 2: Create a new reusable `Icon` component (N/A for backend Python image generation).
    - [ ] Solution 3: Use an icon library (N/A for backend Python image generation).
- [x] **Choose a solution**: Solution 1 was chosen.
- [ ] **Implement the plan**:
    - [x] Located the component responsible for rendering card details (location, date) - this is handled in `api/utils/card_utils.py`.
    - [x] Identified the current icon rendering mechanism (`draw_pin_icon`, `draw_calendar_icon` in Python).
    - [x] Replaced the current rendering with PIL `Image.open()` and `canvas.paste()` for `public/icon_pin.png` and `public/icon_calendar.png` in `api/utils/card_utils.py`.
    - [x] Adjusted styling (size, alignment) for the new icons within the Python script.
    - [x] Verified the paths to the icons (`public/icon_pin.png` and `public/icon_calendar.png`) - hardcoded, with error logging.
    - [ ] Mark old drawing functions as deprecated.
- [ ] **Test**: Manually trigger card generation to ensure the new PNG icons are displayed correctly and that errors are logged if icons are missing.
- [ ] **Cleanup (Optional)**: Remove the deprecated `draw_pin_icon` and `draw_calendar_icon` functions from `api/utils/card_utils.py` after successful testing. 