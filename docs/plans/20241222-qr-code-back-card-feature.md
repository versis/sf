# QR Code Back Card Feature Implementation Plan
*Date: December 22, 2024*

## Problem Statement
Add QR code functionality to the back of postcard designs by placing the provided QR code image (`@sf_qr.png`) in the same column as the existing post stamp but positioned at the bottom of the card.

## Bigger Picture Analysis
This is a postcard generation system where each card has:
- **Front side**: Color swatch + user image with metadata
- **Back side**: Note area + rectangular stamp (top-right) + circular postmark + ruled lines

The enhancement adds a QR code to the back design, positioned consistently in the same column as the stamp for professional postal appearance.

## Possible Solutions Analysis

### Solution 1: Simple Addition (Recommended ✅)
**Approach**: Add QR code loading and positioning logic directly in the `generate_back_card_image_bytes` function.

**Pros**:
- Minimal code changes
- Follows existing pattern (like stamp and postmark implementation)
- No technical debt
- Easy to test and verify

**Cons**:
- Less flexible for future changes
- Hardcoded QR code path

**Implementation**: Add QR code loading after postmark generation, position it at the bottom of the stamp column.

### Solution 2: Configurable QR Code (More Flexible)
**Approach**: Make QR code optional/configurable with parameters.

**Pros**:
- Future-proof for different QR codes
- Can be enabled/disabled per card
- More flexible positioning

**Cons**:
- Over-engineering for current requirements
- Requires API changes
- More complex testing

**Implementation**: Add QR code parameters to card generation functions and models.

### Solution 3: Componentized Approach (Most Maintainable)
**Approach**: Extract all elements (stamp, postmark, QR code) into separate functions.

**Pros**:
- Better code organization
- Easier to maintain and extend
- Unit testable components

**Cons**:
- Significant refactoring required
- Risk of breaking existing functionality
- Longer implementation time

**Implementation**: Refactor back card generation into composable functions.

## Chosen Solution: Solution 1 (Simple Addition)
**Rationale**: The user wants the QR code "always" on the back, which suggests a simple, consistent implementation. Solution 1 provides immediate value without over-engineering.

## Multi-Step Implementation Plan

### Phase 1: Code Analysis & Planning ✅ COMPLETED
- [x] **Step 1.1**: Understand current back card generation logic
- [x] **Step 1.2**: Identify stamp positioning and column calculation
- [x] **Step 1.3**: Analyze QR code file location and format
- [x] **Step 1.4**: Plan positioning strategy

### Phase 2: QR Code Integration ✅ COMPLETED
- [x] **Step 2.1**: Add QR code loading logic to `generate_back_card_image_bytes`
- [x] **Step 2.2**: Calculate QR code size based on stamp dimensions
- [x] **Step 2.3**: Position QR code in same column as stamp, at bottom
- [x] **Step 2.4**: Handle error cases (missing QR file, loading errors)

### Phase 3: Testing & Validation ✅ COMPLETED
- [x] **Step 3.1**: Test QR code positioning with different orientations
- [x] **Step 3.2**: Verify QR code doesn't interfere with other elements
- [x] **Step 3.3**: Test with both PNG and TIFF output formats
- [x] **Step 3.4**: Validate scaling across different card sizes

### Phase 4: Quality Assurance ✅ COMPLETED
- [x] **Step 4.1**: Run linters to check code quality
- [x] **Step 4.2**: Test card generation API endpoints
- [x] **Step 4.3**: Verify backward compatibility
- [x] **Step 4.4**: Document changes for future reference

## Implementation Summary ✅ COMPLETED

**What was implemented:**
1. **Dynamic QR Code Generation**: Added `qrcode[pil]` dependency and `generate_qr_code_image()` function
2. **Reusable Perforation Function**: Extracted `draw_perforation_dots()` to avoid code duplication  
3. **QR Code Logic**: Added dynamic QR code generation, sizing, and positioning after postmark generation
4. **Stamp-Style Design**: QR code styled exactly like the postage stamp with same grey background
5. **Error Handling**: Graceful fallback if QR code generation fails
6. **Code Reuse**: Both stamp and QR code use the same perforation drawing function
7. **Custom Styling**: QR code generated with stamp's grey background instead of white

**Key Features:**
- ✅ QR code appears on all back cards
- ✅ **SAME SIZE as post stamp** (exact dimensions)
- ✅ **SAME BORDER STYLE** (perforation dots pattern)
- ✅ **SAME BACKGROUND** (light gray stamp color)
- ✅ **"CREATE YOUR POSTCARD" CALL-TO-ACTION** above QR code (each word on separate line, aligned with QR code)
- ✅ **MAXIMIZED QR CODE SIZE** (URL text removed to give more space)
- ✅ Positioned in same column as stamp (right side)
- ✅ Positioned at bottom of card with proper padding
- ✅ Scales proportionally with card size
- ✅ Works with both horizontal and vertical orientations
- ✅ Compatible with PNG and TIFF output formats
- ✅ No interference with existing elements
- ✅ Graceful error handling for missing QR file
- ✅ Backward compatibility maintained
- ✅ **NO CODE DUPLICATION** (reusable perforation function)

**Technical Details:**
- QR code size: **Square** (fits within middle area of stamp)
- Background: **Dynamically generated with same grey** as stamp (#F8F9FA)
- Border: Same perforation dots as stamp
- Padding: Same 10% internal padding as stamp logo
- Position: Aligned in stamp column, bottom of card, **centered within stamp**
- **QR Code Data**: `https://shadefreude.com` (as requested)
- **Call-to-Action**: "CREATE YOUR POSTCARD" above QR code (Bold Inter font, each word on separate line, aligned with QR code)
- **Layout**: 2-tier design - CTA at top, maximized QR code below (URL removed for larger QR)
- **Generation**: Dynamic using `qrcode[pil]` library (no static file needed)
- **Aspect Ratio**: Always square (essential for proper QR code scanning)
- **Typography**: Dark text on light background for optimal readability
- **Space Management**: Dynamic sizing to fit all elements within stamp area
- Error handling: Logs error but continues card generation with fallback
- Dependency: Added `qrcode[pil]>=7.4.2` to `pyproject.toml`

## Technical Implementation Details

### QR Code Positioning Strategy
```python
# Position QR code in same column as stamp, at bottom
qr_x_start = stamp_x_start  # Same X coordinate as stamp
qr_y_start = card_h - pad_y - qr_size  # Bottom of card minus padding
qr_size = int(stamp_width * 0.8)  # Slightly smaller than stamp
```

### File Structure Impact
```
api/utils/card_utils.py - Main implementation
├── generate_back_card_image_bytes() - Add QR code logic
└── QR_CODE_PATH constant - Path to sf_qr.png

public/sf_qr.png - QR code asset (existing)
```

### Code Integration Points
1. **QR Code Loading**: After postmark generation, before text processing
2. **Size Calculation**: Based on stamp dimensions for consistency
3. **Positioning**: Same X column as stamp, bottom Y position
4. **Error Handling**: Graceful fallback if QR code missing

### Scaling Considerations
- QR code scales proportionally with card size (like stamp)
- Maintains aspect ratio across orientations
- Works with both PNG and TIFF formats
- Respects card padding and margins

## Success Criteria
- [ ] QR code appears on all back cards
- [ ] QR code positioned in same column as stamp
- [ ] QR code positioned at bottom of card
- [ ] QR code scales appropriately with card size
- [ ] Works with both horizontal and vertical orientations
- [ ] Compatible with PNG and TIFF output formats
- [ ] No interference with existing elements (stamp, postmark, text)
- [ ] Graceful error handling if QR code file missing
- [ ] Backward compatibility maintained
- [ ] Code passes linter checks

## Quality Requirements
- **Consistency**: QR code positioning identical across all cards
- **Scalability**: Proportional sizing based on card dimensions
- **Reliability**: Error handling for missing QR code file
- **Performance**: Minimal impact on card generation time
- **Maintainability**: Clean, readable code following existing patterns

## Testing Strategy
1. **Unit Testing**: Test QR code positioning calculations
2. **Integration Testing**: Test with real card generation flow
3. **Visual Testing**: Verify QR code placement and sizing
4. **Edge Case Testing**: Missing QR file, different orientations
5. **Performance Testing**: Measure impact on generation time

## Risk Mitigation
- **Missing QR File**: Add error handling with graceful fallback
- **Positioning Conflicts**: Ensure adequate spacing from other elements
- **Performance Impact**: Monitor card generation time increases
- **Backward Compatibility**: Test existing cards still generate correctly 