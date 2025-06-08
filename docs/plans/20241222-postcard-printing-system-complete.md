# Postcard Printing System - Complete Implementation Plan
*Date: December 22, 2024*

## Problem Statement
Create a professional print-ready postcard system at 300 DPI with A4 format, supporting 6 cards per page in perfect 1:2 ratio, including cutting guides and double-sided printing alignment.

## Mathematical Requirements (FINALIZED)
- **A4 at 300 DPI:** 2480×3508 pixels (210×297mm)
- **Perfect 1:2 ratio:** 60×120mm per card (709×1417 pixels) ✅
- **3×2 grid layout:** 3 cards wide, 2 cards tall
- **Used space:** 180×240mm (2126×2834 pixels)
- **Cutting margin:** 27mm vertical (318 pixels) for trimming ✅

## Layout Specifications

### A4 Layout with Professional Features
```
A4 Layout (210×297mm):

┌─────────────────────────────────────────────┐
│  15mm margin                                │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐  │ ← Cutting line (grey, dashed)
│  │   CUTTING ZONE (13.5mm)              │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
│  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │ C1   │  │ C2   │  │ C3   │  [FRONT]   │
│  │60×120│  │60×120│  │60×120│            │
│  │ mm   │  │ mm   │  │ mm   │            │
│  └──────┘  └──────┘  └──────┘            │
│  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │ C4   │  │ C5   │  │ C6   │            │
│  │60×120│  │60×120│  │60×120│            │
│  │ mm   │  │ mm   │  │ mm   │            │
│  └──────┘  └──────┘  └──────┘            │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐  │ ← Cutting line (grey, dashed)
│  │   CUTTING ZONE (13.5mm)              │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
│  15mm margin                               │
└─────────────────────────────────────────────┘

BACK SIDE (Short-edge flip alignment):
┌─────────────────────────────────────────────┐
│  ┌──────┐  ┌──────┐  ┌──────┐    [BACK]   │
│  │ C3   │  │ C2   │  │ C1   │  ← Mirrored │
│  │BACK  │  │BACK  │  │BACK  │            │
│  └──────┘  └──────┘  └──────┘            │
│  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │ C6   │  │ C5   │  │ C4   │  ← Mirrored │
│  │BACK  │  │BACK  │  │BACK  │            │
│  └──────┘  └──────┘  └──────┘            │
└─────────────────────────────────────────────┘
```

### Double-Sided Printing Alignment
- **Short-edge flip (book-style):** Recommended for postcards
- **Card arrangement:** Back side horizontally mirrored [0,1,2,3,4,5] → [2,1,0,5,4,3]
- **Alignment verification:** Test patterns included

## Implementation Plan

### Phase 1: Core Card Generation (High-DPI) 
- [x] **Step 1.1:** Update card dimensions to exact 709×1417 pixels (1:2 ratio)
- [x] **Step 1.2:** Implement automatic font scaling preservation
- [ ] **Step 1.3:** Generate TIFF version alongside existing PNG
- [ ] **Step 1.4:** Test single card generation and scaling

### Phase 2: Database Schema Updates
- [ ] **Step 2.1:** Add TIFF URL columns to database
- [ ] **Step 2.2:** Update API models for new fields
- [ ] **Step 2.3:** Implement parallel PNG/TIFF upload
- [ ] **Step 2.4:** Test database integration

### Phase 3: A4 Layout Engine
- [ ] **Step 3.1:** Create basic A4 canvas and card positioning
- [ ] **Step 3.2:** Implement 3×2 grid with exact spacing
- [ ] **Step 3.3:** Add cutting guide lines (grey, dashed)
- [ ] **Step 3.4:** Test single-sided A4 layout generation

### Phase 4: Double-Sided Print Alignment  
- [ ] **Step 4.1:** Implement short-edge flip positioning logic
- [ ] **Step 4.2:** Create back-side layout with mirrored arrangement
- [ ] **Step 4.3:** Add print side indicators (FRONT/BACK labels)
- [ ] **Step 4.4:** Test front/back alignment with numbered test cards

### Phase 5: Print Utilities & API
- [ ] **Step 5.1:** Create print utility functions
- [ ] **Step 5.2:** Add API endpoint for A4 generation
- [ ] **Step 5.3:** Implement local file generation tool
- [ ] **Step 5.4:** Test complete print workflow

### Phase 6: Integration & Testing
- [ ] **Step 6.1:** Integrate with existing card generation flow
- [ ] **Step 6.2:** Add frontend controls (if needed)
- [ ] **Step 6.3:** Performance optimization and error handling
- [ ] **Step 6.4:** Final print quality validation

## Technical Specifications

### Print Layout Constants
```python
# Core dimensions
PRINT_DPI = 300
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
CARD_WIDTH_MM = 60          # Perfect for 1:2 ratio
CARD_HEIGHT_MM = 120

# Layout spacing
A4_MARGINS_MM = 15          # Outer A4 margins
CUTTING_ZONE_MM = 13.5      # Top/bottom cutting areas
CARD_SPACING_MM = 0         # No spacing between cards

# Cutting guides
CUTTING_LINE_COLOR = "#CCCCCC"
CUTTING_LINE_OPACITY = 0.2
CUTTING_LINE_WIDTH = 0.5    # Points
CUTTING_LINE_DASH = (2, 1)  # mm dash, mm gap

# Double-sided printing
FLIP_MODE = "short_edge"    # Book-style recommended
PRINT_ALIGNMENT = True      # Enable back-side mirroring
```

### File Structure
```
api/utils/
├── card_utils.py (existing)
├── print_utils.py (new) ← Will implement step by step
└── print_layout.py (new)

api/routers/
└── print_generation.py (new)

scripts/
└── local_print_generator.py (new)
```

### Database Schema Changes
```sql
-- Add TIFF URL columns
ALTER TABLE card_generations ADD COLUMN front_horizontal_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN front_vertical_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN back_horizontal_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN back_vertical_tiff_url TEXT;
```

## Quality Requirements
- **Resolution:** 300 DPI minimum
- **File formats:** TIFF (print), PNG (web)
- **Color space:** RGB (TIFF supports CMYK conversion)
- **File size:** <15MB per A4 sheet
- **Processing time:** <45 seconds per sheet
- **Print compatibility:** Standard short-edge duplex printing

## Testing Strategy
- **Step-by-step validation** after each implementation phase
- **Visual verification** with numbered test cards
- **Print alignment testing** with actual print samples
- **Performance benchmarking** for processing times
- **Backward compatibility** with existing PNG workflow

## Success Criteria
- [ ] Generate exact 1:2 ratio cards at 300 DPI
- [ ] Professional cutting guides included
- [ ] Perfect front/back alignment for duplex printing
- [ ] Complete backward compatibility maintained
- [ ] Local generation tool for easy testing
- [ ] Print-shop ready TIFF outputs 