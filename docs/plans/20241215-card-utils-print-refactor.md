# Card Utils Print Quality Refactor

## Summary
Refactored `card_utils.py` to improve TIFF generation at exactly 300 DPI with precise passepartout sizing.

## Issues Addressed

### 1. Precision Loss in Calculations
- **Problem**: Using `int()` truncation caused inaccuracies in dimensions
- **Solution**: Use `round()` for proper rounding instead of truncation
- **Impact**: Improved passepartout accuracy by 0.030mm, height by 0.062mm

### 2. Passepartout Size Issues
- **Problem**: 7mm passepartout was actually 6.943mm due to truncation
- **Solution**: Pre-calculated exact pixel dimensions with proper rounding
- **Result**: Now 7.027mm (within 0.027mm tolerance)

### 3. Inconsistent Dimension Calculations
- **Problem**: Dimensions calculated on-the-fly, potentially inconsistent
- **Solution**: Pre-calculated constants for all TIFF dimensions
- **Benefit**: Consistent, predictable results across all generations

## Changes Made

### New Constants
```python
# Pre-calculated TIFF dimensions (using proper rounding for exact 300 DPI)
CARD_CONTENT_WIDTH_PX = 1535   # 129.963mm actual
CARD_CONTENT_HEIGHT_PX = 3071  # 260.011mm actual
PASSEPARTOUT_PX = 83           # 7.027mm actual
CARD_TIFF_WIDTH = 1701         # Final width with passepartout
CARD_TIFF_HEIGHT = 3237        # Final height with passepartout
```

### Accuracy Verification
- **Content width error**: 0.037mm (within tolerance)
- **Content height error**: 0.011mm (within tolerance)  
- **Passepartout error**: 0.027mm (within tolerance)
- **All dimensions within 0.1mm tolerance** ✅

### Improved Logging
- Added detailed TIFF dimension logging
- Physical dimensions displayed in mm alongside pixels
- Print dimension verification function for debugging

## Verification Results

### Before (int truncation):
- Content: 1535 x 3070 px = 129.963 x 259.927 mm
- Passepartout: 82 px = 6.943 mm (0.057mm error)

### After (proper rounding):
- Content: 1535 x 3071 px = 129.963 x 260.011 mm  
- Passepartout: 83 px = 7.027 mm (0.027mm error)

## Testing
Run `uv run python verify_print_dimensions.py` to verify calculations and accuracy.

## Status
- [x] Fix precision issues in dimension calculations
- [x] Pre-calculate TIFF dimensions as constants  
- [x] Improve passepartout accuracy from 6.943mm to 7.027mm
- [x] Add detailed logging for TIFF generation
- [x] Create verification script
- [x] All dimensions within 0.1mm tolerance
- [x] Document improvements

## Impact
Cards now print at exactly 300 DPI with precise physical dimensions, ensuring professional print quality with accurate 7mm passepartout borders. 