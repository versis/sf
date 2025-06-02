# Fix Card Back Line Color Issue

**Date:** 2024-12-20  
**Bug:** The lines on the back of the card should be the same color as text, not the same as user chosen color.

## Problem Analysis

The card back lines are currently using the user's selected hex color instead of using a consistent text color. This creates visual inconsistency and potentially poor contrast, especially when the chosen color doesn't contrast well with the card background.

## Possible Solutions

### Solution 1: Hardcoded Text Color for Lines
- Set all lines on card backs to use a fixed color (e.g., black, dark gray)
- Ensure good contrast with the card background
- Maintain visual consistency across all cards

### Solution 2: Dynamic Color Based on Background
- Calculate appropriate line color based on card background lightness
- Use black lines on light backgrounds, white lines on dark backgrounds
- Implement contrast ratio checking for accessibility

### Solution 3: Theme-Based Line Color
- Use a predefined color scheme for card backs
- Separate line color from user's chosen color completely
- Consider card design aesthetics and readability

## Recommended Solution

**Solution 2** is most prominent because it ensures optimal readability while maintaining design flexibility and accessibility standards.

## Multi-Step Plan

### Step 1: Locate Card Back Generation Code
- [ ] Find the backend code that generates card back images
- [ ] Identify where line colors are currently set
- [ ] Document current color selection logic

### Step 2: Analyze Current Color Usage
- [ ] Test current behavior with various user-selected colors
- [ ] Identify cases where contrast is poor
- [ ] Document which colors cause readability issues

### Step 3: Implement Color Contrast Logic
- [ ] Create a function to determine optimal line color based on background
- [ ] Implement contrast ratio calculations
- [ ] Set minimum contrast requirements for accessibility

### Step 4: Update Line Rendering
- [ ] Replace user color with calculated line color in card generation
- [ ] Ensure all text elements (lines, text) use the same color logic
- [ ] Maintain consistency between note text and line colors

### Step 5: Test Across Color Spectrum
- [ ] Test with light colors (whites, yellows, pastels)
- [ ] Test with dark colors (blacks, dark blues, etc.)
- [ ] Test with medium saturation colors
- [ ] Verify readability in all cases

### Step 6: Design Validation
- [ ] Ensure visual appeal is maintained
- [ ] Check that cards look professional
- [ ] Validate with design principles for card layouts

### Step 7: Accessibility Testing
- [ ] Test with color blindness simulators
- [ ] Verify WCAG contrast guidelines are met
- [ ] Ensure text remains readable for all users 