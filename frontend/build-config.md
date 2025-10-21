# Cloudflare Pages Build Configuration

## Framework Settings
- **Framework preset:** Vite
- **Build command:** `npm run build`
- **Build output directory:** `dist`
- **Root directory (monorepo builds):** `frontend`

## Environment Variables
No environment variables required for frontend build.

## Important Notes
1. **Do NOT set a deploy command** - Cloudflare Pages automatically deploys the contents of the build output directory
2. The error "Deployment handled by Cloudflare Pages" means someone entered that text as a deploy command - it should be empty
3. Build process:
   - `npm clean-install` (automatic)
   - `npm run build` (runs TypeScript + Vite)
   - Deploy `dist/` folder contents

## Troubleshooting
If deployment fails:
1. Check that build output directory is set to `dist`
2. Verify build command is exactly: `npm run build`
3. Ensure deploy command is **empty** (not "Deployment handled by Cloudflare Pages")
4. Confirm root directory is `frontend` if using monorepo structure

## Build Performance Note
Build shows warning about 940 kB chunk size. This is acceptable for now but consider:
- Code splitting with dynamic imports
- Manual chunk configuration
- Lazy loading routes

Current build time: ~8 seconds ✓
