# EleutherIA Visual Assets Index

Complete catalog of infographics, videos, and branding materials for the EleutherIA project.

---

## 📊 Infographics

### Production-Ready SVGs

All infographics follow the EleutherIA design system (sage green #769687, academic serif fonts, warm paper backgrounds).

| File | Dimensions | Purpose | Best Used For |
|------|------------|---------|---------------|
| **graphrag-workflow.svg** | 1200×800 | 6-step GraphRAG process explanation | Documentation, README, blog posts |
| **database-architecture.svg** | 1400×900 | Triple-threat system architecture | Technical docs, presentations |
| **multi-modal-integration.svg** | 1200×1000 | Circular integration diagram | Conceptual explanations, papers |

**Location**: `/assets/infographics/`

**Documentation**: See `/assets/infographics/README.md` for usage guidelines, export instructions, and customization tips.

---

## 🎬 Video Storyboards

### GraphRAG Explainer Video

**Status**: Storyboard complete, ready for production

**Storyboard file**: `/assets/video-storyboards/graphrag-explainer-storyboard.md`

**Specifications**:
- Duration: 90-120 seconds (60s social media version available)
- Resolution: 1920×1080 (Full HD)
- Style: Academic motion graphics
- Format: 11 scenes with detailed timing, visuals, voiceover scripts

**Scenes**:
1. Title card (5s)
2. The challenge (10s)
3. User question (7s)
4. Step 1: Semantic search (10s)
5. Step 2: Graph traversal (13s)
6. Step 3: Context assembly (10s)
7. Step 4: LLM generation (10s)
8. Final answer (13s)
9. The difference (10s)
10. Closing & coverage (7s)
11. End card (10s)

**Production options**:
- DIY: 20-40 hours, $0-200 (Manim, Blender, After Effects)
- Professional: 1-2 weeks, $1,500-5,000

---

## 🎨 Branding Assets

### Logos

| File | Format | Transparency | Use Case |
|------|--------|--------------|----------|
| **logo-svg.svg** | SVG | No | Light backgrounds |
| **logo-transparent-svg.svg** | SVG | Yes | Any background |

**Location**: `/assets/branding/`

### Favicons & Icons

| File | Size | Purpose |
|------|------|---------|
| favicon.ico | 16×16, 32×32 | Browser tab icon |
| favicon-16x16.png | 16×16 | Browser fallback |
| favicon-32x32.png | 32×32 | Browser fallback |
| apple-touch-icon.png | 180×180 | iOS home screen |
| android-chrome-192x192.png | 192×192 | Android home screen |
| android-chrome-512x512.png | 512×512 | Android splash screen |
| og-image.png | 1200×630 | Social media previews (Open Graph) |

**Location**: `/frontend/public/`

---

## 🎨 Design System Reference

### Color Palette

```css
/* Primary Colors */
--sage-green-50:  #f3f7f5;
--sage-green-100: #e2ebe7;
--sage-green-200: #c5d7cf;
--sage-green-300: #a8c3b7;
--sage-green-400: #8baf9f;
--sage-green-500: #769687;  /* Brand color */
--sage-green-600: #769687;
--sage-green-700: #5d7769;
--sage-green-800: #475a4f;
--sage-green-900: #313d36;

/* Academic Neutrals */
--academic-bg:     #fafaf9;
--academic-paper:  #ffffff;
--academic-text:   #1c1917;
--academic-muted:  #78716c;
--academic-border: #e7e5e4;
```

### Typography

**Primary**: Georgia, serif
**Greek/Latin**: Palatino Linotype, Book Antiqua, Palatino, serif
**Fallback**: Times New Roman, serif

**Scale**:
- H1: 36-42px, bold
- H2: 28-32px, bold
- H3: 20-24px, semibold
- Body: 14-16px, regular
- Caption: 11-13px, regular

### Visual Effects

**Shadows** (elevation):
```css
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);  /* Soft */
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);   /* Medium */
box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25); /* Strong */
```

**Border radius**: 8-12px for cards, 4-6px for buttons

**Gradients**:
- Paper: `linear-gradient(#ffffff → #fafaf9)`
- Sage: `linear-gradient(#769687 → #8baf9f)`

---

## 📐 Templates & Guidelines

### Creating New Infographics

1. **Start with color palette** - Use sage green (#769687) and academic neutrals
2. **Use Georgia serif** - All text should be in Georgia
3. **Add Greek/Latin examples** - Use Palatino font, italic for Latin
4. **Include soft shadows** - Elevate important elements
5. **Academic footer** - Always include license (CC BY 4.0)

**SVG Template structure**:
```xml
<svg width="1200" height="800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Gradients, filters, markers here -->
  </defs>

  <!-- Background -->
  <rect fill="#fafaf9" />

  <!-- Content with filters -->
  <g filter="url(#shadow)">
    <!-- Your content -->
  </g>

  <!-- Footer -->
  <text font-family="Georgia, serif" fill="#78716c">
    EleutherIA | CC BY 4.0
  </text>
</svg>
```

### Video Production Checklist

- [ ] Script approved
- [ ] Storyboard illustrated
- [ ] Assets gathered (logos, fonts, permissions)
- [ ] Voiceover recorded
- [ ] Animation produced
- [ ] Music licensed and integrated
- [ ] Captions/subtitles added (accessibility)
- [ ] Review & feedback incorporated
- [ ] Exported in multiple formats
- [ ] Published and embedded in docs

---

## 🔄 Export Workflows

### SVG → PNG (High Resolution)
```bash
# Using Inkscape (recommended)
inkscape input.svg --export-png=output.png --export-dpi=300

# Using ImageMagick
convert -density 300 input.svg output.png
```

### SVG → PDF (LaTeX/Academic Papers)
```bash
inkscape input.svg --export-pdf=output.pdf
```

### SVG → Video Frame
```bash
# 1080p for video
inkscape input.svg --export-png=frame.png --export-width=1920 --export-height=1080
```

### Creating Animated GIFs
For social media previews:
```bash
# 1. Create PNG sequence
# 2. Convert to GIF
convert -delay 10 -loop 0 frame-*.png output.gif

# 3. Optimize
gifsicle -O3 output.gif -o optimized.gif
```

---

## 📝 Usage Examples

### In README.md
```markdown
## How GraphRAG Works

![GraphRAG Workflow](./assets/infographics/graphrag-workflow.svg)

The system combines semantic search, graph traversal, and LLM synthesis...
```

### In Documentation Site
```html
<figure>
  <img src="/assets/infographics/database-architecture.svg"
       alt="EleutherIA Database Architecture"
       width="100%" />
  <figcaption>
    Triple-threat architecture: Knowledge Graph, PostgreSQL, Vector Database
  </figcaption>
</figure>
```

### In Academic Paper (LaTeX)
```latex
\begin{figure}[ht]
  \centering
  \includegraphics[width=\textwidth]{assets/infographics/multi-modal-integration.pdf}
  \caption{Multi-modal integration in EleutherIA:
           seamless data flow across three modalities.}
  \label{fig:integration}
\end{figure}
```

### In Presentations
- **Google Slides**: Insert → Image → Upload (SVG works natively)
- **PowerPoint**: Insert → Pictures (export to PNG at 2x resolution for best quality)
- **Keynote**: Drag and drop SVG directly

---

## 🌐 Social Media Assets

### Open Graph Preview
**File**: `/frontend/public/og-image.png` (1200×630px)

Used for:
- Twitter/X cards
- Facebook link previews
- LinkedIn shares
- Discord embeds

### Profile Pictures / Avatars
Use the transparent logo at various sizes:
- 400×400px (Twitter/X)
- 500×500px (LinkedIn)
- 180×180px (GitHub)

### Video Thumbnails
Export key frame from video (Scene 8 recommended):
- YouTube: 1280×720px
- Twitter: 1200×675px
- LinkedIn: 1200×627px

---

## 📜 Licensing

All visual assets are licensed under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

### Attribution Format

**For infographics**:
```
EleutherIA Infographic by Romain Girardi
CC BY 4.0 License
https://github.com/yourusername/ancient-free-will-database
```

**For videos**:
```
EleutherIA: Ancient Free Will Database
Created by Romain Girardi
Licensed under CC BY 4.0
```

### Permitted Uses
✅ Commercial and non-commercial use
✅ Remix, adapt, build upon
✅ Redistribute in any format

**Requirement**: Provide attribution to Romain Girardi and EleutherIA project

---

## 🔗 Quick Links

| Asset Type | Location | Documentation |
|------------|----------|---------------|
| Infographics | `/assets/infographics/` | `/assets/infographics/README.md` |
| Video storyboards | `/assets/video-storyboards/` | `/assets/video-storyboards/graphrag-explainer-storyboard.md` |
| Logos | `/assets/branding/` | This file |
| Favicons | `/frontend/public/` | This file |
| Web assets | `/frontend/public/` | This file |

---

## 🎯 Roadmap

### Completed ✅
- [x] GraphRAG workflow infographic
- [x] Database architecture diagram
- [x] Multi-modal integration diagram
- [x] Video storyboard for GraphRAG explainer
- [x] Design system documentation

### Planned 🔮
- [ ] Animated GIF version of GraphRAG workflow (for social media)
- [ ] Timeline infographic: 4th c. BCE → 6th c. CE coverage
- [ ] Concept map: Key philosophical terms (ἐφ' ἡμῖν, εἱμαρμένη, etc.)
- [ ] Database statistics dashboard (interactive visualization)
- [ ] 60-second video for Twitter/X and LinkedIn
- [ ] 3-minute deep dive video for YouTube
- [ ] Influence network visualization (Aristotle → Stoics → Patristics)

### Ideas for Contribution 💡
- Comparison chart: EleutherIA vs. other philosophical databases
- Researcher persona infographic (use cases)
- API integration diagram
- Search comparison (keyword vs. semantic vs. GraphRAG)

---

## 📧 Contact

**Maintainer**: Romain Girardi
**Email**: romain.girardi@univ-cotedazur.fr
**ORCID**: 0000-0002-5310-5346

For requests, feedback, or collaboration on visual assets, please reach out!

---

**Last updated**: 2025
**Version**: 1.0.0
