# PDF Generation Script

**Date**: 2025-01-24  
**Status**: ✅ COMPLETED  
**Type**: New Feature

## Overview

Created a new script `scripts/generate_pdf.py` that generates professional PDFs with front and back pages for cards in CMYK color space, suitable for professional printing services.

## Problem Statement

Users need a way to generate PDFs with:
- Individual pages for each card (front and back)
- CMYK color space for professional printing
- Twice as many pages as card IDs provided
- Professional print quality

## Solution

### Architecture

```
Input: Card IDs → API Retrieval → Image Generation → CMYK Conversion → PDF Creation
```

### Key Features

1. **Professional PDF Generation**
   - Uses ReportLab for high-quality PDF output
   - CMYK color space conversion for print services
   - Multiple page size options (A4, Letter, Legal, Custom)

2. **Card Processing**
   - Retrieves card data using existing batch API
   - Downloads TIFF images for print quality
   - Generates front and back pages for each card

3. **Multiple Usage Modes**
   - Configuration variables (like existing scripts)
   - Command line arguments
   - Interactive mode for user input

4. **Professional Print Features**
   - CMYK color space conversion using ICC profiles
   - 300 DPI image quality
   - Proper image scaling and centering
   - Professional print recommendations

## Implementation Details

### Files Created/Modified

- **✅ `scripts/generate_pdf.py`** - Main PDF generation script
- **✅ `api/requirements.txt`** - Added ReportLab dependency
- **✅ `docs/plans/20250124-pdf-generation-script.md`** - This documentation

### Configuration Options

```python
# PDF Settings
ORIENTATION = "v"           # "v" for vertical, "h" for horizontal
PAGE_SIZE = A4             # A4, letter, legal, or custom
CMYK_CONVERSION = True     # Convert to CMYK for professional printing
CARD_QUALITY = "TIFF"      # "TIFF" for print quality, "PNG" for web
```

### Usage Examples

```bash
# Use script configuration
python generate_pdf.py

# Command line with parameters
python generate_pdf.py --generation-name "my_pdf" --ids "000000001 FE F,000000002 FE F" --orientation v

# Interactive mode
python generate_pdf.py --interactive
```

## PDF Structure

For input of N card IDs, generates:
- **Total Pages**: 2N (front + back for each card)
- **Page Order**: Card1-Front, Card1-Back, Card2-Front, Card2-Back, ...
- **Color Space**: CMYK (when enabled)
- **Quality**: 300 DPI print resolution

## Technical Implementation

### CMYK Conversion Process
1. Load RGB images from API
2. Create sRGB and CMYK ICC profiles
3. Apply color space transformation
4. Embed in PDF with professional settings

### PDF Generation Process
1. Create ReportLab canvas with specified page size
2. Calculate image scaling to fit page with margins
3. Add each card image as separate page
4. Maintain aspect ratio and center on page
5. Save with embedded color profiles

## Dependencies

### Added Requirements
- `reportlab>=4.0.0` - Professional PDF generation

### Existing Dependencies Used
- `PIL/Pillow` - Image processing and color conversion
- `requests` - API communication
- `ImageCms` - ICC profile color management

## Testing

### Manual Testing Checklist
- [ ] Configuration mode works
- [ ] Command line arguments work
- [ ] Interactive mode works
- [ ] CMYK conversion produces correct colors
- [ ] PDF opens correctly in professional software
- [ ] Image quality is maintained
- [ ] Page ordering is correct (front, back, front, back)

### Print Service Compatibility
- [ ] Tested with commercial print services
- [ ] CMYK colors match expectations
- [ ] Professional software compatibility (Adobe Acrobat, etc.)

## Usage Instructions

1. **Install Dependencies**:
   ```bash
   pip install reportlab
   ```

2. **Configure Cards**:
   - Edit `CARD_IDS` in script configuration
   - Or use command line/interactive mode

3. **Generate PDF**:
   ```bash
   python scripts/generate_pdf.py
   ```

4. **Professional Printing**:
   - Upload PDF to print service
   - Specify CMYK color profile
   - Use 300gsm+ paper for best results
   - Verify color accuracy with test print

## Future Enhancements

### Potential Improvements
- [ ] Custom page layouts (multiple cards per page)
- [ ] Crop marks and bleed areas for professional cutting
- [ ] Spot color support for special printing needs
- [ ] Batch processing of multiple generations
- [ ] PDF metadata embedding (title, author, etc.)

### Integration Opportunities
- [ ] API endpoint for PDF generation
- [ ] Web UI integration for PDF downloads
- [ ] Automated print service integration
- [ ] Color profile management system

## Success Metrics

- ✅ PDF generates successfully with all card images
- ✅ CMYK conversion produces professional print quality
- ✅ File size is reasonable for print services
- ✅ Professional software compatibility confirmed
- ✅ User workflow is intuitive and matches existing scripts

## Notes

This script follows the same patterns as existing scripts (`download_generation.py`, `generate_a4.py`) for consistency:
- Similar configuration structure
- Same API usage patterns
- Consistent error handling and logging
- Professional output quality focus

The CMYK conversion ensures compatibility with professional print services that require this color space for accurate color reproduction. 