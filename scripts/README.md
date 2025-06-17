# Scripts Directory

This directory contains utility scripts for working with card generations.

## Available Scripts

1. **`download_generation.py`** - Download individual TIFF cards (front and back)
2. **`generate_a4.py`** - Generate A4 layouts for professional printing (3 cards per sheet)
3. **`generate_pdf.py`** - Generate PDF with individual pages (front and back for each card) in CMYK color space
4. **`generate-hero-cache.js`** - Generate hero image cache for the website

---

## generate_pdf.py

**NEW!** Generates professional PDFs with front and back pages for cards in CMYK color space, perfect for professional printing services.

### Quick Start

```bash
# Make sure both servers are running first
# Terminal 1: Start Next.js server
pnpm dev

# Terminal 2: Start Python API server  
uvicorn api.index:app --reload

# Generate PDF using command line
uv run python scripts/generate_pdf.py \
  --generation-name "my_pdf" \
  --ids "000000001 FE F,000000002 FE F" \
  --orientation v

# Or use interactive mode
uv run python scripts/generate_pdf.py --interactive
```

### Key Features

- **Professional PDF Output**: Individual pages for each card (front + back)
- **CMYK Color Space**: Perfect for professional printing services
- **Multiple Page Sizes**: A4, US Letter, US Legal, or custom sizes
- **High Quality**: 300 DPI print resolution maintained
- **Flexible Input**: Command line, interactive mode, or script configuration

### Usage Options

1. **Command Line Mode**:
   ```bash
   uv run python scripts/generate_pdf.py \
     --generation-name "my_pdf" \
     --ids "000000001 FE F,000000002 FE F" \
     --orientation v
   ```

2. **Interactive Mode**:
   ```bash
   uv run python scripts/generate_pdf.py --interactive
   ```

3. **Configuration Mode**:
   - Edit variables in the script
   - Run: `uv run python scripts/generate_pdf.py`

### Parameters

- `--generation-name` / `-g`: Name for the PDF file
- `--ids` / `-i`: Comma-separated list of card IDs
- `--orientation` / `-o`: Card orientation (`v` for vertical, `h` for horizontal)
- `--interactive`: Run in interactive mode

### Output

- **File Location**: `data/pdf_generations/<generation_name>.pdf`
- **Page Structure**: For N cards → 2N pages (Card1-Front, Card1-Back, Card2-Front, Card2-Back, ...)
- **Color Space**: CMYK (when enabled)
- **Quality**: 300 DPI print resolution

### Professional Printing

The generated PDFs are optimized for professional printing:
- CMYK color space for accurate color reproduction
- Embedded ICC color profiles
- High-resolution images (300 DPI)
- Proper image scaling and centering

---

## download_generation.py

Downloads TIFF cards (front and back) for specific card IDs, organizing them into generation-specific directories.

### Quick Start

```bash
# Make sure both servers are running first
# Terminal 1: Start Next.js server
pnpm dev

# Terminal 2: Start Python API server  
uvicorn api.index:app --reload

# Then download cards using command line
uv run python scripts/download_generation.py \
  --generation-name "my_generation" \
  --ids "000000001 FE F,000000002 FE F,000000003 FE F" \
  --orientation v

# Or use interactive mode
uv run python scripts/download_generation.py --interactive
```

### Usage Options

1. **Command Line Mode** (recommended for automation):
   ```bash
   uv run python scripts/download_generation.py \
     --generation-name "generation_name" \
     --ids "000000001 FE F,000000002 FE F" \
     --orientation v  # or h for horizontal
   ```

2. **Interactive Mode** (user-friendly):
   ```bash
   uv run python scripts/download_generation.py --interactive
   ```

3. **Configuration Mode** (edit script variables):
   - Edit the configuration variables at the top of `download_generation.py`
   - Run: `uv run python scripts/download_generation.py`

### Parameters

- `--generation-name` / `-g`: Name for the generation directory
- `--ids` / `-i`: Comma-separated list of card IDs (e.g., "000000001 FE F,000000002 FE F")
- `--orientation` / `-o`: Card orientation (`v` for vertical, `h` for horizontal)
- `--interactive`: Run in interactive mode

### Output

Files are saved to: `data/generations_single/<generation_name>/`

File naming format:
- `<simple_id>-front.tiff` (e.g., `000000001-front.tiff`)
- `<simple_id>-back.tiff` (e.g., `000000001-back.tiff`)

Where `<simple_id>` is the 9-digit ID extracted from the extended ID format.

### Examples

```bash
# Download vertical cards for a specific generation
uv run python scripts/download_generation.py \
  --generation-name "christmas_2024" \
  --ids "000000101 FE F,000000102 FE F,000000103 FE F" \
  --orientation v

# Download horizontal cards
uv run python scripts/download_generation.py \
  --generation-name "landscape_cards" \
  --ids "000000201 FE F,000000202 FE F" \
  --orientation h

# Interactive mode - prompts for all inputs
uv run python scripts/download_generation.py --interactive
```

### Requirements

- Both servers must be running:
  1. Next.js server: `pnpm dev` (port 3000)
  2. Python API server: `uvicorn api.index:app --reload` (port 8000)
- Dependencies are managed via `uv` (automatically installed)

### Troubleshooting

If you get "API not reachable" or "500 error":
1. Make sure BOTH servers are running:
   - Next.js server: `pnpm dev` (port 3000)
   - Python API server: `uvicorn api.index:app --reload` (port 8000)
2. Check that the API_BASE_URL in the script matches your Next.js server (default: `http://localhost:3000/api`)

If cards are not found:
1. Verify the card IDs exist in the database
2. Check that the extended ID format is correct (e.g., "000000001 FE F")
3. Ensure the cards have been fully generated (status = "completed") 