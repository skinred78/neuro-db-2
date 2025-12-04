# Phase 3 Summary: Wider Configuration Scope

**Status**: ✅ Plan Complete (appended to `251203-flask-webapp-plan.md`)
**Lines Added**: ~595 lines
**Date**: 2025-12-03

---

## What Changed

Extended Flask webapp plan from **2 fixed configs** → **5 selectable configs** with parallel execution.

---

## New Configurations

1. **NeuroDB-Only** - Neuroscience abbreviations only (no classification)
2. **UMLS-Only** - Semantic classification only (no disambiguation)
3. **PubTator-Only** - Biomedical disambiguation only (no classification)
4. **UMLS+PubTator** - 2-layer (existing, proven POC)
5. **FullHybrid** - 3-layer (existing, NeuroDB + PubTator + UMLS)

---

## Key Features

### User Experience
- Checkbox selection (2-5 configs)
- Client-side validation
- Responsive grid (2-5 columns)
- Article overlap highlighting across N configs

### Backend
- `ConfigFactory` for config instantiation
- `ThreadPoolExecutor` for parallel execution (3-5s vs 6-10s sequential)
- Partial failure handling (one config crashes → others still display)
- Graceful fallbacks for unresolved terms

### Architecture
```
Single-layer configs reuse existing clients:
- NeuroDBOnly: Loads abbreviation dict (no UMLS/PubTator clients)
- UMLSOnly: Loads UMLSClient only (no disambiguation)
- PubTatorOnly: Loads PubTatorClient only (no classification)
```

---

## Implementation Checklist

- [ ] Add 3 new config classes (`test_configurations.py`)
- [ ] Add `ConfigFactory` class (`test_configurations.py`)
- [ ] Update route handler for multi-select + parallel (`app.py`)
- [ ] Add checkbox UI (`index.html`)
- [ ] Dynamic grid layout (`results.html`)
- [ ] Responsive CSS (`style.css`)
- [ ] Test all 5 configs individually
- [ ] Test 2-config, 3-config, 5-config comparisons
- [ ] Verify fallback behavior

---

## Unresolved Questions

1. **Config naming**: Full names ("Full Hybrid") vs layer counts ("3-Layer")?
   - **Rec**: Descriptive names

2. **Default selections**: Which configs checked by default?
   - **Rec**: `umls_pubtator + full_hybrid` (proven baselines)

3. **Performance warning**: Warn if 5 configs + many keywords?
   - **Rec**: Limit keywords to 5 if 5 configs selected

4. **Article overlap**: "Unique" = only in 1 config or in minority?
   - **Rec**: Strict unique (only in 1)

5. **Fallback indicator**: Show badge when term unresolved?
   - **Rec**: Add "⚠️ Fallback" badge for UNKNOWN categories

---

## Performance Impact

**Phase 1+2**: Sequential execution
- UMLSPubTator: 3-5s
- FullHybrid: 3-5s
- **Total**: 6-10s

**Phase 3**: Parallel execution
- 5 configs in parallel: 3-5s
- **Improvement**: 2x-3x faster

**API Usage**:
- Only UMLS-based configs consume quota
- PubTator: no key required
- NeuroDB: local file

---

## Files Modified

```
poc_api_first/
├── tests/test_configurations.py   [MAJOR] 3 new configs + factory
├── webapp/
│   ├── app.py                     [MAJOR] parallel execution
│   ├── templates/
│   │   ├── index.html             [MODERATE] checkbox UI
│   │   └── results.html           [MODERATE] dynamic grid
│   └── static/
│       └── style.css              [MINOR] grid + checkbox styles
```

---

## Next Steps

1. Review Phase 3 plan in main file (line ~792 onwards)
2. Implement new config classes
3. Test single-layer configs for fallback behavior
4. Implement parallel execution
5. Test responsiveness with 2-5 columns
