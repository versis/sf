# Scripts Directory

This directory contains utility scripts for working with card generations.

## download_generation.py

Downloads TIFF cards (front and back) for specific card IDs, organizing them into generation-specific directories.

### Quick Start

```bash
# Make sure the API is running first
uvicorn api.index:app --reload

# Download cards using command line
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

- API server must be running: `uvicorn api.index:app --reload`
- Dependencies are managed via `uv` (automatically installed)

### Troubleshooting

If you get "API not reachable" error:
1. Make sure the API server is running: `uvicorn api.index:app --reload`
2. Check that the API_BASE_URL in the script matches your server (default: `http://localhost:8000/api`)

If cards are not found:
1. Verify the card IDs exist in the database
2. Check that the extended ID format is correct (e.g., "000000001 FE F")
3. Ensure the cards have been fully generated (status = "completed") 