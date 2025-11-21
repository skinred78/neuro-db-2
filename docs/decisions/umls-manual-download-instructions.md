# UMLS Manual Download Instructions

**Issue**: UMLS files require license authentication - cannot download via curl/wget

**Solution**: Manual download through UTS (UMLS Terminology Services) portal

---

## Download Steps

### 1. Log in to UTS
Visit: https://uts.nlm.nih.gov/uts/login

Use your UMLS license credentials (the ones you got approval for).

### 2. Navigate to Downloads
After login, visit: https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html

Or click: **Downloads** → **UMLS Knowledge Sources**

### 3. Download the File
Find the row:
```
UMLS Metathesaurus Full Subset
File: umls-2025AB-metathesaurus-full.zip
Size: 5.2 GB (compressed) → 35.8 GB (uncompressed)
```

Click the download link.

**Checksum (to verify after download)**:
```
MD5: 494e5ab4a9b0cb5c60f40fea999abef4
```

### 4. Save to Project Directory
Save the downloaded ZIP file to:
```
/Users/sam/NeuroDB-2/downloads/umls/2025AB/umls-2025AB-metathesaurus-full.zip
```

---

## After Download

Once downloaded, let me know and I'll:
1. Verify the checksum
2. Extract the files
3. Verify all 4 required RRF files are present
4. Proceed with Phase 2 (build neuroscience CUI filter)

---

## Alternative: Check Existing Downloads

If you've already downloaded UMLS files previously, let me know the location and I can verify if they're usable.

Common locations:
- `~/Downloads/`
- `~/Documents/UMLS/`
- Desktop

I can search for existing UMLS files if you'd like.
