# Plan: Update Hero Section Content (2025-01-03)

## Problem Statement
We need to update the hero section with new content that includes:
- **New Title**: "Your Everyday Photos, Having Their Moment"
- **New Subtitle**: "Polaroid vibes. AI brains. No cringe (usually)."
- **New Description**: Multi-sentence description about picking colors from photos and creating digital postcards
- **Styling**: Appropriate font sizes and hierarchy for the new subtitle element

## Current Structure Analysis
The hero section is located in `app/(dashboard)/page.tsx` around lines 1345-1370. Currently it has:
- A complex title with spans and line breaks
- A single paragraph description
- No subtitle element

## Possible Solutions

### Solution 1: Simple Text Replacement
- Replace existing title and description text directly
- Add subtitle as a new element between title and description
- Use existing styling patterns

### Solution 2: Restructured Typography Hierarchy
- Redesign the text hierarchy with proper semantic structure
- Create distinct styling for title, subtitle, and description
- Improve responsive typography scaling

### Solution 3: Component-Based Approach
- Extract hero text into a separate component
- Create reusable typography components
- Better maintainability for future content updates

## Prominent Solution: Solution 2 - Restructured Typography Hierarchy
This approach provides the best balance of immediate needs and future maintainability while improving the overall design hierarchy.

## Implementation Steps

- [x] **Create Plan Document**: Document the approach and steps
- [x] **Analyze Current Styling**: Review existing Tailwind classes and responsive behavior
- [x] **Update Hero Content**: Replace title, add subtitle, update description
- [x] **Implement Typography Hierarchy**: 
  - Main title: Large, bold, primary text (`text-2xl md:text-3xl lg:text-4xl font-bold`)
  - Subtitle: Medium, lighter weight, muted color (`text-lg md:text-xl font-medium text-muted-foreground`)
  - Description: Standard size, muted color for readability (`text-md md:text-lg text-muted-foreground leading-relaxed`)
- [x] **Test Responsive Behavior**: Ensure proper scaling on mobile and desktop
- [x] **Verify Visual Hierarchy**: Confirm the content flows well and is readable

## Implementation Summary

Successfully updated the hero section with:

### Typography Hierarchy
- **Main Title**: `text-2xl md:text-3xl lg:text-4xl font-bold mb-2 md:mt-6 text-foreground`
  - "Your Everyday Photo, Having Its Moment"
- **Subtitle**: `text-base md:text-lg font-normal mb-4 text-muted-foreground/90 tracking-wide`  
  - "Polaroid vibes. AI brains. No cringe (usually)."
- **Description**: `text-md md:text-lg text-muted-foreground leading-relaxed`
  - Multi-sentence description about the color-picking experience

### Technical Details
- Fixed apostrophe escaping issue (`didn't` → `didn&apos;t`)
- Maintained responsive design with proper mobile/desktop scaling
- Preserved existing layout structure and button positioning
- All linting errors resolved (only warnings remain, which are acceptable)

### Visual Improvements
- Clear hierarchy with distinct font sizes and weights
- Improved readability with `leading-relaxed` on description
- Proper color contrast using `text-foreground` and `text-muted-foreground`
- Responsive scaling from mobile (`text-2xl`) to desktop (`lg:text-4xl`)

## Content Details

**New Title**: "Your Everyday Photos, Having Their Moment"
**New Subtitle**: "Polaroid vibes. AI brains. No cringe (usually)."
**New Description**: 
"Pick a color from your photo. Watch it become a digital postcard with a custom color name and an observation you didn't see coming. Each color tells its own story. Add a note on the back if you want. The kind of thing you share, print, or both."

## Typography Considerations
- Title should be prominent but not overwhelming
- Subtitle should feel playful and approachable
- Description should be easily scannable with good line spacing
- Maintain consistency with existing design system 