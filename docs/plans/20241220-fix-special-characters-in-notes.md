# Fix Special Characters in Notes Issue

**Date:** 2024-12-20  
**Bug:** We cannot render emojis etc on the back of the cards - do not allow them. I think we should only allow only keyboard letters.

## Problem Analysis

The card generation backend cannot properly render emojis and special characters on the card backs, likely due to font limitations or text rendering constraints. The solution is to implement input validation to only allow standard keyboard characters (letters, numbers, basic punctuation) in note inputs.

## Possible Solutions

### Solution 1: Frontend Input Filtering
- Add real-time input filtering on the textarea
- Block non-standard characters as user types
- Provide immediate feedback when invalid characters are entered

### Solution 2: Backend Validation with Sanitization
- Implement server-side validation for allowed characters
- Strip or replace invalid characters automatically
- Return validation errors for client handling

### Solution 3: Combined Frontend and Backend Validation
- Filter inputs on frontend for immediate feedback
- Validate and sanitize on backend as security measure
- Provide clear error messages for rejected characters

## Recommended Solution

**Solution 3** is most prominent because it provides the best user experience with immediate feedback while maintaining data integrity and security through backend validation.

## Multi-Step Plan

### Step 1: Define Allowed Character Set
- [ ] Define exactly which characters are allowed (a-z, A-Z, 0-9, basic punctuation)
- [ ] Consider international characters (accented letters, etc.)
- [ ] Create a whitelist regex pattern for validation
- [ ] Document the character restrictions for users

### Step 2: Implement Frontend Validation
- [ ] Add input filtering to the note textarea in `app/(dashboard)/page.tsx`
- [ ] Create real-time validation on text input
- [ ] Show visual feedback for invalid characters
- [ ] Update character counter to reflect validation

### Step 3: Add User Feedback
- [ ] Display clear error messages for rejected characters
- [ ] Update placeholder text to mention character restrictions
- [ ] Consider showing allowed characters in a tooltip or help text
- [ ] Provide suggestions for alternative characters

### Step 4: Implement Backend Validation
- [ ] Add character validation to the note submission endpoint
- [ ] Create server-side sanitization functions
- [ ] Return specific error messages for character violations
- [ ] Log attempts to submit invalid characters for monitoring

### Step 5: Update Input UI
- [ ] Modify the textarea styling to indicate validation state
- [ ] Add visual indicators for valid/invalid input
- [ ] Consider showing remaining character count with validation status
- [ ] Update the submit button state based on validation

### Step 6: Handle Edge Cases
- [ ] Deal with copy-paste operations containing invalid characters
- [ ] Handle different keyboard layouts and input methods
- [ ] Consider mobile keyboard variations
- [ ] Test with screen readers and accessibility tools

### Step 7: Testing and Validation
- [ ] Test with various emoji inputs
- [ ] Test with special Unicode characters
- [ ] Test copy-paste operations from different sources
- [ ] Verify backend card generation works with all allowed characters
- [ ] Test across different browsers and devices

### Step 8: Documentation and User Education
- [ ] Update user-facing help text about note formatting
- [ ] Document the technical limitations in developer docs
- [ ] Consider adding a "why this restriction?" explanation for users
- [ ] Update any relevant error handling documentation

**Status:** ❌ **PENDING** - Implementation reverted, needs rework.

## Technical Implementation Notes

### Frontend Implementation
```typescript
// Character validation regex (example)
const ALLOWED_CHARS_REGEX = /^[a-zA-Z0-9\s.,!?'";:()-]*$/;

// Input handler with validation
const handleNoteTextChange = (value: string) => {
  if (ALLOWED_CHARS_REGEX.test(value)) {
    setNoteText(value);
    setValidationError(null);
  } else {
    setValidationError("Only letters, numbers, and basic punctuation allowed");
  }
};
```

### Backend Implementation
```python
# Character validation function
def validate_note_text(text: str) -> bool:
    import re
    allowed_pattern = r'^[a-zA-Z0-9\s.,!?\'";:()-]*$'
    return re.match(allowed_pattern, text) is not None
``` 