# Creating GitHub Release for Zenodo DOI

## Current Status
✅ Tag `v1.0.0` already exists on GitHub (commit 3af3332)
❌ Release not yet published

## Steps to Complete Release

### 1. Go to Release Creation Page
https://github.com/romain-girardi-eng/EleutherIA/releases/new

### 2. Fill in Release Form

**Tag:**
- Select existing tag: `v1.0.0` (should appear in dropdown)
- Or just type: `v1.0.0` - it will recognize the existing tag

**Release Title:**
```
EleutherIA v1.0.0 - Ancient Free Will Database
```

**Description:**
Copy the entire content from `RELEASE_NOTES_v1.0.0.md` into the description field.

### 3. Publish Release
- Click "Publish release" button (green button at bottom)
- DO NOT save as draft

### 4. Verify Zenodo Integration

After publishing:
1. Go to your Zenodo account: https://zenodo.org/account/settings/github/
2. Check if EleutherIA repository appears
3. Toggle it ON if not already enabled
4. The release should automatically sync to Zenodo
5. Zenodo will assign a DOI (usually within a few minutes)

### 5. After DOI is Assigned

Once Zenodo assigns the DOI (format: `10.5281/zenodo.XXXXXXX`), update these files:

**README.md** - Add DOI badge at top:
```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

**CITATION.cff** - Update doi field:
```yaml
doi: 10.5281/zenodo.XXXXXXX
```

**codemeta.json** - Update identifier field:
```json
"identifier": "https://doi.org/10.5281/zenodo.XXXXXXX"
```

**All citation examples** - Replace `[ZENODO-DOI-HERE]` with actual DOI

### Troubleshooting

**If you see what looks like "2 releases":**
- One might be a draft release (unpublished)
- Go to: https://github.com/romain-girardi-eng/EleutherIA/releases
- Delete any draft releases
- Keep only the published v1.0.0 release

**If tag v1.0.0 doesn't appear:**
- It exists remotely (confirmed)
- Just type `v1.0.0` manually in the tag field

**If Zenodo doesn't sync:**
- Check repository is enabled in Zenodo settings
- Check webhook is active: Repository Settings → Webhooks
- Should see Zenodo webhook URL
- If missing, re-toggle repository in Zenodo settings

---

## Quick Summary

1. ✅ Tag v1.0.0 already exists (commit 3af3332)
2. 📝 Create release at: https://github.com/romain-girardi-eng/EleutherIA/releases/new
3. 📋 Copy content from RELEASE_NOTES_v1.0.0.md
4. ✅ Publish (not draft!)
5. 🔍 Wait for Zenodo DOI assignment
6. 📝 Update all files with DOI when assigned

---

**Current commit with tag:** 3af3332 (docs: Add v1.0.0 release notes for Zenodo publication)
