# Open Graph & Social Media Setup

**Status:** ✅ Complete
**Date:** 2025-10-18
**Domain:** https://free-will.app

## What Was Fixed

### Before
- Title: "frontend" (not descriptive)
- Description: None (showed "frontend" on WhatsApp)
- Preview Image: No image displayed
- Favicon: Generic Vite logo

### After
- **Title:** "EleutherIA - Ancient Free Will Database"
- **Description:** "A revolutionary digital humanities platform combining Knowledge Graph, PostgreSQL, and AI-powered semantic search. Explore ancient philosophical debates on free will from Aristotle to Augustine."
- **Preview Image:** EleutherIA logo (1200x630 PNG) - optimized for all social platforms
- **Favicon:** EleutherIA logo

## Changes Made

### 1. Frontend Meta Tags (`frontend/index.html`)

Added comprehensive meta tags:

```html
<!-- Primary Meta Tags -->
<title>EleutherIA - Ancient Free Will Database</title>
<meta name="description" content="..." />
<meta name="keywords" content="ancient philosophy, free will, determinism..." />

<!-- Open Graph / Facebook / WhatsApp -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://free-will.app/" />
<meta property="og:title" content="EleutherIA - Ancient Free Will Database" />
<meta property="og:description" content="..." />
<meta property="og:image" content="https://free-will.app/og-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />

<!-- Twitter Cards -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:image" content="https://free-will.app/og-image.png" />

<!-- SEO -->
<link rel="canonical" href="https://free-will.app/" />
<meta name="robots" content="index, follow" />
```

### 2. Social Media Preview Image

Created `og-image.png`:
- **Dimensions:** 1200x630px (optimal for all platforms)
- **Format:** PNG (better compatibility than SVG)
- **Size:** 67 KB
- **Source:** Converted from `logo.svg` using librsvg

### 3. Backend Improvements

Enhanced `backend/services/hybrid_search.py`:
- Added proper error handling for `GEMINI_API_KEY`
- Added dotenv loading for environment variables
- Added logging for API key status

## Files Added/Modified

### New Files
- `frontend/public/og-image.png` - Social media preview image (1200x630 PNG)

### Modified Files
- `frontend/index.html` - Added all meta tags
- `backend/services/hybrid_search.py` - Improved API key handling

### Build Output (auto-generated, not committed)
- `frontend/dist/index.html` - Built version with meta tags
- `frontend/dist/og-image.png` - Copy of preview image
- `frontend/dist/logo.svg` - Copy of logo

## How to Test

### 1. Deploy to Production

After deploying the updated `dist` folder to https://free-will.app:

### 2. Test with WhatsApp
1. Open WhatsApp (mobile or web)
2. Send a message with: `https://free-will.app`
3. Wait for the preview to load
4. You should see:
   - **Title:** "EleutherIA - Ancient Free Will Database"
   - **Description:** "Explore ancient philosophical debates..."
   - **Image:** EleutherIA logo

### 3. Test with Facebook Debugger
```
https://developers.facebook.com/tools/debug/
```
- Enter: `https://free-will.app`
- Click "Scrape Again" to refresh cache
- Verify all meta tags are detected

### 4. Test with Twitter Card Validator
```
https://cards-dev.twitter.com/validator
```
- Enter: `https://free-will.app`
- Verify "summary_large_image" card displays correctly

### 5. Test with LinkedIn Post Inspector
```
https://www.linkedin.com/post-inspector/
```
- Enter: `https://free-will.app`
- Verify preview displays correctly

### 6. Test with Generic OG Checker
```
https://www.opengraph.xyz/
https://metatags.io/
```
- Enter: `https://free-will.app`
- Verify all Open Graph properties

## Important: Deployment Notes

### Files That MUST Be Deployed

Make sure these files are on your server:

```
dist/
├── index.html          (with new meta tags)
├── og-image.png        (1200x630 PNG)
├── logo.svg            (for favicon)
└── assets/             (JS and CSS files)
```

### Cache Clearing

After deployment, you may need to clear caches:

1. **WhatsApp:** May take 5-10 minutes to refresh
2. **Facebook:** Use the Debug Tool to force refresh
3. **Twitter:** Use Card Validator to force refresh
4. **LinkedIn:** Use Post Inspector to force refresh

### Server Configuration

Ensure your server serves these files:
- `og-image.png` must be accessible at: `https://free-will.app/og-image.png`
- `logo.svg` must be accessible at: `https://free-will.app/logo.svg`

If using a CDN or special routing, verify the paths are correct.

## Troubleshooting

### Image Not Showing
- Verify `https://free-will.app/og-image.png` loads in browser
- Check image is at least 200x200px (ours is 1200x630 ✅)
- Check image is less than 8MB (ours is 67KB ✅)
- Clear cache using platform debug tools

### Wrong Title/Description
- Verify `index.html` has been deployed
- Use browser "View Source" to confirm meta tags
- Clear platform caches

### Still Shows "frontend"
- You haven't deployed the new `dist/index.html` yet
- Browser/platform is using cached version
- Force refresh using platform debug tools

## SEO Benefits

Beyond social media, these changes improve:
- **Google Search Results:** Better title and description snippets
- **Browser Bookmarks:** Proper title instead of "frontend"
- **Browser Tabs:** Descriptive title
- **Search Engine Indexing:** Canonical URL and proper metadata

## Next Steps (Optional)

Consider adding:
- Specific OG tags for individual pages (e.g., `og:image` per node)
- Structured data (JSON-LD) for rich snippets
- Additional SEO meta tags (geo location, language alternates)
- Custom Twitter handle (`twitter:site` and `twitter:creator`)

---

**Commit:** a01e5d5
**Status:** ✅ Committed and pushed to main
