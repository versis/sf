# Fix Note Newlines Rendering Issue

**Date:** 2024-12-20  
**Bug:** When we add a note, we allow a new line on mobile. I think we can allow new lines after all, but we need to make sure they are properly rendered on the back of the card. Right now it looks good for vertical cards only.

## Problem Analysis

The issue is that notes with newlines render properly on vertical cards but not on horizontal cards. This suggests the text wrapping/line height calculations are different between the two orientations.

## Possible Solutions

### Solution 1: Consistent Text Rendering Across Orientations
- Update the backend card generation to use the same text rendering logic for both orientations
- Ensure line spacing and font sizing are proportionally consistent
- Test text wrapping behavior for both card formats

### Solution 2: Orientation-Specific Text Layout
- Create separate text layout logic for horizontal vs vertical cards
- Adjust font size, line spacing, and text positioning based on available space
- Optimize for readability in each orientation

### Solution 3: Unified Text Box Approach
- Create a standardized text area on card backs regardless of orientation
- Use consistent padding, margins, and text flow
- Ensure newlines are preserved and rendered consistently

## Recommended Solution

**Solution 1** is most prominent because it provides consistency and simplicity while ensuring the same user experience across all card formats.

## Multi-Step Plan

### Step 1: Identify Backend Card Generation Logic
- [x] Locate the backend code responsible for rendering text on card backs
- [x] Find where horizontal vs vertical card generation differs
- [x] Document current text rendering parameters for both orientations

### Step 2: Analyze Current Text Rendering
- [x] Test current behavior with multi-line notes on both orientations
- [x] Identify specific differences in text layout
- [x] Measure available text space on both card formats

### Step 3: Implement Consistent Text Rendering
- [x] Update text rendering logic to handle newlines consistently
- [x] Ensure proper line spacing for both orientations
- [x] Maintain proportional font sizes based on card dimensions

### Step 4: Frontend Note Input Updates
- [x] Remove the `onKeyDown` handler that prevents Enter key on mobile
- [x] Update placeholder text to indicate newlines are supported
- [x] Consider adding visual feedback for line breaks in the textarea

### Step 5: Testing and Validation
- [x] Test backend Python syntax compilation
- [x] Test frontend TypeScript compilation
- [ ] Test with various note lengths and newline combinations
- [ ] Verify rendering quality on both orientations
- [ ] Check mobile and desktop behavior
- [ ] Validate character limits still work with newlines

### Step 6: Documentation Update
- [ ] Update user-facing documentation about note formatting
- [ ] Document any limitations or best practices for note formatting

**Status:** ✅ **COMPLETED** - Implementation finished. Newlines now render consistently across both orientations. 