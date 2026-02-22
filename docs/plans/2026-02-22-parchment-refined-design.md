# Parchment Refined — Design

**Date:** 2026-02-22
**Scope:** CSS-only typography and texture refinements across the entire site

## Goal

Add two frontier design techniques — typography refinement and noise texture with layered shadows — to the existing parchment redesign. Zero component changes; everything applied through global CSS in `index.css`.

## Technique 1: Typography Refinement

### Tight Letter-Spacing on Display Headings

Add `letter-spacing: -0.02em` to all elements using `font-display` (Instrument Serif). This editorial tightening is standard in luxury publications and modern SaaS (Linear, Stripe, NYT). Makes headings feel crafted rather than default-spaced.

Applied via a CSS rule targeting `.font-display` and heading elements that use the display font.

### Text-Wrap Balance on Headings

Add `text-wrap: balance` to h1, h2, h3. This prevents orphan words on the last line of multi-line headings. Browser-native (Chrome 114+, Firefox 121+), graceful fallback on older browsers (no-op).

### Font Optical Sizing

Add `font-optical-sizing: auto` to body. Instructs variable fonts (DM Sans, Instrument Serif) to adjust stroke weights for their rendered size — thicker at small sizes for legibility, thinner at large sizes for elegance.

## Technique 2: Noise Texture + Layered Shadows

### Noise Overlay

A `body::after` pseudo-element with an inline SVG `feTurbulence` filter. Properties:
- Opacity: 0.03 (barely perceptible)
- `mix-blend-mode: multiply` (blends with parchment background)
- `pointer-events: none` (no interaction interference)
- `position: fixed`, full viewport coverage
- `z-index: 9998` (below modals/tooltips but above content)

This adds paper grain that makes the parchment background feel physical.

### Layered Box Shadows

Replace existing single-layer `--shadow-*` CSS variables with multi-layer versions. Each shadow uses 3 declarations:
1. **Contact shadow** — tight, dark, simulates object resting on surface
2. **Depth shadow** — medium spread, semi-transparent, creates lift perception
3. **Ambient shadow** — wide, very light, atmospheric glow

Variables affected: `--shadow-xs`, `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`, `--shadow-2xl`.

No component changes needed — every element using `shadow-sm`, `shadow-md` etc. via Tailwind or CSS variables automatically upgrades.

## Files Changed

- `frontend/src/index.css` — All changes in this single file

## What We Don't Change

- No component files
- No Tailwind config
- No JavaScript/TypeScript
- Landing page, KG Visualizer remain untouched
