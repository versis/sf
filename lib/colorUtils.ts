export function getContrastTextColor(hexColor: string | null | undefined): string {
  if (!hexColor) return '#000000'; // Default to black if no color is provided

  // Remove # if present
  const hex = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;

  // Expand shorthand hex (e.g., "03F") to full form (e.g., "0033FF")
  const fullHex = hex.length === 3 ? hex.split('').map(char => char + char).join('') : hex;
  
  if (fullHex.length !== 6) {
    // Invalid hex color format after attempting to expand
    return '#000000'; // Default to black for invalid hex
  }

  try {
    const r = parseInt(fullHex.slice(0, 2), 16);
    const g = parseInt(fullHex.slice(2, 4), 16);
    const b = parseInt(fullHex.slice(4, 6), 16);

    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

    // Return black for light backgrounds, white for dark backgrounds
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
  } catch (error) {
    // Error during parsing (should be rare with length check)
    return '#000000'; // Default to black on error
  }
} 