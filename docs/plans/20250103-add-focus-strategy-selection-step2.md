# Plan: Maximize Lower Dimension in Step 2 - January 3, 2025

## Problem Statement
Change step 2 ("Frame your focus") to automatically maximize the lower dimension (smaller of width or height) to create the largest possible square crop, instead of the current fixed 1:1 square aspect ratio.

## Bigger Picture Analysis
- Current implementation uses fixed 1:1 aspect ratio for all crops
- Users need more control over how their images are framed
- "Maximizing lower dimension" suggests strategy-based approach rather than fixed ratios
- This enhances user experience by providing meaningful cropping options

## Files Involved
- `app/(dashboard)/page.tsx` - Main dashboard with step 2 implementation
- `components/ImageUpload.tsx` - The cropping component  
- New component: `components/FocusStrategySelector.tsx` - UI for strategy selection

## Chosen Solution: Automatic Lower Dimension Maximization
Automatically use the smaller dimension (min of width and height) to create the largest possible square crop without user selection options.

## Implementation Steps

### Phase 1: Modify ImageUpload Component ✅ COMPLETED
- [x] Update `components/ImageUpload.tsx`
  - [x] Remove focus strategy props and imports
  - [x] Simplify aspect ratio calculation to always use 1:1
  - [x] Update crop initialization to use maximized square approach
  - [x] Ensure minimum dimension requirements are still enforced

### Phase 2: Update Dashboard Integration ✅ COMPLETED
- [x] Modify `app/(dashboard)/page.tsx`
  - [x] Remove focus strategy state and handlers
  - [x] Remove FocusStrategySelector from step 2 UI
  - [x] Simplify ImageUpload component usage
  - [x] Clean up unused imports and props

### Phase 3: Cleanup ✅ COMPLETED
- [x] Remove unused FocusStrategySelector component
- [x] Update plan documentation

## Expected Behavior ✅ COMPLETED
1. User uploads image in step 1
2. Step 2 automatically initializes cropper to maximize the lower dimension
3. Cropper creates the largest possible square crop using the smaller dimension
4. Minimum 900x900px requirement is still enforced
5. User proceeds to step 3 with optimally cropped image

## Technical Notes
- Crop initialization automatically uses the smaller of width/height for maximum square area
- Minimum dimension enforcement takes precedence over maximization
- No user selection needed - automatic optimization
- Maintains backward compatibility with existing 1:1 aspect ratio 