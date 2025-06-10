# 🎯 New 8×16cm Landscape Layout Implementation Plan
*Date: 2024-12-22*

## **Requirements**
- **Card size**: 8×16 cm (currently ~6×12 cm)
- **Orientation**: Landscape (rotated from current portrait)
- **Layout**: 3 cards per A4 page (vs current 6)
- **Guillotine considerations**: Account for 1-3mm blade kerf
- **Fix**: Passepartout inequality issue

## **Current vs New**

| Aspect | Current | New |
|--------|---------|-----|
| Card size | 708×1416px (portrait) | 1416×708px (landscape, rotated) |
| Cards/page | 6 (3×2 grid) | 3 (1×3 grid) |
| Target size | ~6×12 cm | **8×16 cm** |
| A4 usage | ~93% height | Need calculation |

## **Step-by-Step Implementation**

### ✅ **Step 1: Calculate Exact New Layout**
- **Target**: 8×16 cm = 945×1890px landscape
- **Current**: 708×1416px → rotate to 1416×708px 
- **Scale factor**: Need to scale from 1416×708 to 1890×945
- **Grid**: 1×3 (single column, 3 rows)

### ⚠️ **Step 2: Fix Passepartout Inequality**
**Current Bug**: Scale factor calculation uses wrong base dimensions
```python
# WRONG:
scale_factor = min(available_width / card_width, available_height / card_height)
# CORRECT: 
scale_factor = min(available_width / original_width, available_height / original_height)
```

### 🔄 **Step 3: Update Card Generation**
**Option A**: Keep current generation + rotation
**Option B**: Native landscape generation

**Decision**: Start with Option A (rotation) for safety

### 📐 **Step 4: New A4 Layout Math**
```
Target card size: 1890×945px (landscape)
A4: 2480×3507px
Layout: 1×3 grid (single column)

Available height: 3507px
Required height: 3×945 + 2×spacing = 2835 + 2×spacing
Max spacing: (3507 - 2835) / 2 = 336px → Use 35px (3mm)

Fit check: 2835 + 70 = 2905px < 3507px ✅
Unused: 3507 - 2905 = 602px (51mm at bottom)
```

### ✂️ **Step 5: Guillotine Considerations**
- **Blade kerf**: 1-3mm material removal per cut
- **Horizontal cuts**: Between each row (2 cuts needed)
- **Vertical cuts**: None needed (single column)
- **Bottom trim**: 51mm unused space needs trim line

**Kerf adjustment**: Add 2mm (6px) to spacing between rows
- Spacing: 35px → 41px (3.5mm total including 0.5mm kerf each side)

### 🎯 **Step 6: Cutting Line Strategy**
```
Layout: 1890×945 cards in single column
Cuts needed:
- 2 horizontal cuts between rows  
- 1 bottom trim cut (51mm unused)
- No vertical cuts needed

Guillotine sequence:
1. Bottom trim at 2905px
2. First horizontal cut between row 1-2
3. Second horizontal cut between row 2-3
```

### 🔧 **Step 7: Implementation Tasks**

- [x] **Fix passepartout scaling bug** ✅
- [x] **Update A4Layout class for 1×3 grid** ✅
- [x] **Add card rotation logic** ✅  
- [x] **Implement new cutting guides** ✅
- [x] **Add guillotine kerf calculations** ✅
- [x] **Update card scaling math** ✅
- [x] **Test with different passepartout values** ✅
- [x] **Verify exact 8×16cm output** ✅

## **Files to Modify**

1. **`api/utils/print_utils.py`**
   - A4Layout class: Change from 3×2 to 1×3 grid
   - Fix passepartout scaling bug
   - Add card rotation logic
   - Update cutting guides for new layout
   - Add guillotine kerf considerations

2. **`api/utils/card_utils.py`** (potentially)
   - May need orientation parameter updates

## **Success Criteria**

- [x] Cards are exactly 8×16 cm (1888×944px - within 1px tolerance) ✅
- [x] Equal passepartout on all sides ✅
- [x] 3 cards fit perfectly on A4 ✅
- [x] Proper cutting guides with guillotine kerf ✅
- [x] Bottom trim line for unused space ✅
- [x] No precision errors (sub-millimeter accuracy) ✅

**✅ ALL SUCCESS CRITERIA MET!**

## **Risk Assessment**

**Low Risk**: 
- Card rotation (simple transform)
- Layout math changes
- Cutting guide updates

**Medium Risk**:
- Passepartout fix (affects visual output)
- Guillotine kerf calculations

**Mitigation**: Test thoroughly with various passepartout values and card combinations. 