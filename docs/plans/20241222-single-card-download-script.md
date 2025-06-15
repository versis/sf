# Single Card Generation Download Script

**Date:** 2024-12-22
**Status:** Completed ✅

## Problem Statement

Create a script that allows downloading individual TIFF cards (front and back) for specific card IDs, with the ability to:
- Accept generation name, list of card IDs, and orientation as input
- Create organized directory structure in `data/generations_single/<generation_name>`
- Download TIFF versions of cards in specified orientation
- Rename files to simplified format: `<simple_id>-front.tiff` and `<simple_id>-back.tiff`

## Implementation Plan

### Phase 1: Core Script Development ✅
- [x] Create `scripts/download_generation.py` based on existing `generate_a4.py` pattern
- [x] Implement card retrieval using batch API endpoint
- [x] Add file download functionality with progress reporting
- [x] Implement extended ID to simple ID conversion
- [x] Add directory creation and file organization

### Phase 2: User Interface Enhancement ✅  
- [x] Add command-line argument support
- [x] Implement interactive mode for user-friendly input
- [x] Maintain configuration-based mode for script editing
- [x] Add comprehensive help and examples

### Phase 3: Error Handling & Validation ✅
- [x] API connectivity checks
- [x] Input validation for all parameters
- [x] Graceful handling of missing cards
- [x] File download error handling
- [x] Progress reporting and status updates

## Technical Details

### Script Features
1. **Multiple Usage Modes:**
   - Configuration editing (edit script variables)
   - Command-line arguments
   - Interactive mode

2. **API Integration:**
   - Uses `/batch-retrieve-cards` endpoint for efficient data retrieval
   - Supports both horizontal and vertical orientations
   - Downloads TIFF format for print quality

3. **File Management:**
   - Creates organized directory structure
   - Converts extended IDs (`000000057 FE F`) to simple IDs (`000000057`)
   - Names files as `<simple_id>-front.tiff` and `<simple_id>-back.tiff`

### Usage Examples

```bash
# Command-line usage
python download_generation.py --generation-name "my_generation" --ids "000000001 FE F,000000002 FE F" --orientation v

# Interactive mode
python download_generation.py --interactive

# Configuration mode (edit script variables)
python download_generation.py
```

## File Structure

```
data/generations_single/
└── <generation_name>/
    ├── 000000001-front.tiff
    ├── 000000001-back.tiff
    ├── 000000002-front.tiff
    └── 000000002-back.tiff
```

## Implementation Status

- [x] Core functionality implemented
- [x] Multiple interface modes working
- [x] Error handling comprehensive  
- [x] Documentation complete
- [x] Ready for use

## Next Steps

The script is ready for production use. Future enhancements could include:
- Batch processing from CSV files
- Progress bars for large downloads
- Resume functionality for interrupted downloads
- Integration with existing workflow automation 