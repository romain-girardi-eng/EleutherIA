# EleutherIA Infographics

Beautiful, academically-styled visual explanations of the EleutherIA system.

## Design System

All infographics follow the **EleutherIA visual identity**:

### Color Palette
- **Primary Sage Green**: `#769687` (brand color)
- **Academic Neutrals**:
  - Paper white: `#ffffff`
  - Background: `#fafaf9`
  - Text: `#1c1917`
  - Muted text: `#78716c`
  - Border: `#e7e5e4`
- **Accent Greens**: `#8baf9f`, `#c5d7cf`, `#f3f7f5`

### Typography
- **Headings**: Georgia, serif (bold)
- **Body text**: Georgia, serif (regular)
- **Greek/Latin**: Palatino, serif (italic for Latin)
- **Technical**: Georgia, serif (monospace avoided for academic feel)

### Visual Style
- Clean, scholarly aesthetic
- Soft shadows for elevation
- Rounded corners (8-12px radius)
- Elegant gradients
- Academic paper texture

## Available Infographics

### 1. GraphRAG Workflow (`graphrag-workflow.svg`)
**Dimensions**: 1200×800px
**Purpose**: Explains the 6-step GraphRAG process from user query to scholarly response

**Key features**:
- Step-by-step visual flow
- Data source annotations
- Key features sidebar
- Real example with Greek text (ἐφ' ἡμῖν)
- Citation format demonstration

**Best for**:
- Documentation pages
- Academic presentations
- README files
- Blog posts explaining GraphRAG

---

### 2. Database Architecture (`database-architecture.svg`)
**Dimensions**: 1400×900px
**Purpose**: Shows the triple-threat architecture and unified research workflow

**Key features**:
- Three main components (KG, PostgreSQL, Vector DB)
- Integration connections with bidirectional arrows
- 4-step unified workflow
- Comprehensive statistics
- Historical period coverage

**Best for**:
- Technical documentation
- System architecture presentations
- Research proposals
- Database design discussions

---

### 3. Multi-Modal Integration (`multi-modal-integration.svg`)
**Dimensions**: 1200×1000px
**Purpose**: Circular diagram showing seamless data flow between all three modalities

**Key features**:
- Central hub design emphasizing unity
- Bidirectional connections with data flow labels
- Lateral connections showing cross-component integration
- Example query flow at bottom
- "Provides" annotations for each connection

**Best for**:
- Conceptual explanations
- Integration documentation
- Academic papers
- User-facing documentation

---

## Usage

### In Markdown
```markdown
![GraphRAG Workflow](./assets/infographics/graphrag-workflow.svg)
```

### In HTML
```html
<img src="./assets/infographics/graphrag-workflow.svg"
     alt="GraphRAG Workflow"
     width="100%" />
```

### In LaTeX/Academic Papers
Export to PDF or high-resolution PNG first:
```bash
# Using Inkscape (if installed)
inkscape graphrag-workflow.svg --export-pdf=graphrag-workflow.pdf

# Or use online converters
# https://cloudconvert.com/svg-to-pdf
```

### In Presentations
- SVGs work directly in modern presentation software (Google Slides, PowerPoint 365, Keynote)
- For older software, export to PNG at 2x or 3x resolution for clarity

---

## Exporting to Other Formats

### High-Resolution PNG
```bash
# Using Inkscape
inkscape input.svg --export-png=output.png --export-dpi=300

# Using ImageMagick (if available)
convert -density 300 input.svg output.png
```

### PDF (for LaTeX)
```bash
inkscape input.svg --export-pdf=output.pdf
```

### Video Frames
For video production, export PNGs at consistent dimensions:
```bash
inkscape graphrag-workflow.svg --export-png=frame.png --export-width=1920 --export-height=1080
```

---

## Design Principles

### Academic Rigor
- All text content is accurate and grounded in the actual system
- Statistics are real (509 nodes, 820 edges, 289 texts, etc.)
- Citations follow scholarly conventions
- Greek/Latin terms with proper Unicode characters

### Visual Hierarchy
1. **Title** (largest, bold) - immediate understanding
2. **Section headings** (medium, bold) - guide the eye
3. **Body text** (regular) - detailed information
4. **Annotations** (smaller, italic/muted) - supplementary details

### Accessibility
- High contrast text (WCAG AA compliant)
- Clear visual flow (left-to-right, top-to-bottom)
- Meaningful color usage (not relying solely on color)
- Readable font sizes (minimum 10px for body text)

---

## Customization

To create new infographics following the EleutherIA style:

1. **Use the color palette** (see above)
2. **Apply the shadow filter** for elevation:
   ```xml
   <filter id="cardShadow">
     <feGaussianBlur in="SourceAlpha" stdDeviation="5"/>
     <feOffset dx="0" dy="3"/>
     <!-- ... -->
   </filter>
   ```
3. **Use Georgia serif** for all text
4. **Add Greek/Latin examples** where appropriate (Palatino font)
5. **Include academic footer** with license (CC BY 4.0)

---

## License

All infographics are licensed under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

You are free to:
- **Share** — copy and redistribute
- **Adapt** — remix, transform, build upon

Under these terms:
- **Attribution** — You must give appropriate credit to Romain Girardi and EleutherIA

---

## Credits

**Designer**: Based on EleutherIA brand guidelines
**Maintainer**: Romain Girardi (romain.girardi@univ-cotedazur.fr)
**Created**: 2025
**Tool**: Hand-crafted SVG with academic precision
