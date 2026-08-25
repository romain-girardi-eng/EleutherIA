# `components/the-debate`

Presentational components for `/the-debate`. Nothing here fetches, routes or
holds page state: every component takes props and renders. `TheDebatePage.tsx`
and `theDebateCorpus.ts` are untouched by this folder, and the types here are
deliberately narrower than the page's own `Thinker`, so an object from the
corpus module is structurally assignable without an import in either direction.

```
chronology.ts        pure maths for the rail (tested)
tone.ts              the palette, the leading, the orthography override
types.ts             Tone, ThinkerLike, Locus, LocusState
ChronoRail.tsx       the debate drawn to scale, silence included
CylinderAndSphere.tsx  the editorial centrepiece
BilingualLocus.tsx   the facing-page reading unit
ThinkerStation.tsx   one figure, composed
ContestedField.tsx   the cross-cutting band
DebateOutro.tsx      the hand-off, with nothing resolved
```

All Tailwind, no inline `style`, `cn()` throughout, `prefers-reduced-motion`
handled in every animated component.

---

## The palette, in one paragraph

`Tone` is `'greek' | 'latin' | 'meta'` and it encodes **the language of the
source**, nothing else. Greek is Aegean `#1E4D6B` (8.6:1 on parchment), Latin
is terracotta ink `#B44A12` (5.1:1), `meta` is a sage ink `#44513F` (8.0:1)
reserved for the modern-scholarship layer. All three clear AA for body text,
which is the point: the hue is allowed to touch running prose, so it can carry
a finding instead of decorating a chip. The finding it carries is that the
argument is Greek until Augustine and Latin after him. Focus is expressed as
value, never as a fourth hue.

---

## Wiring

### 1. Page shell

Parchment ground, continuous document, no mandatory scroll snap.

```tsx
<MotionConfig reducedMotion="user">
  <main className="bg-parchment-50 text-stone-900">
    <div className="mx-auto grid max-w-[92rem] gap-x-14 px-6 py-16 lg:px-10
                    xl:grid-cols-[17rem_minmax(0,1fr)]">
      <div className="hidden xl:block">
        <div className="sticky top-20 h-[min(46rem,calc(100dvh-8rem))]">
          <ChronoRail stations={STATIONS} ghosts={GHOSTS} arcs={ARCS}
                      activeId={activeId} />
        </div>
      </div>

      <div className="min-w-0 space-y-32">
        <ChronoRail stations={STATIONS} ghosts={GHOSTS}
                    orientation="horizontal" activeId={activeId}
                    className="sticky top-16 z-10 bg-parchment-50 py-3 xl:hidden" />
        {/* stations, band, outro */}
      </div>
    </div>
  </main>
</MotionConfig>
```

The rail column wants **at least 17rem**; below that the ghost names in the
left gutter start to clip. The vertical rail scales uniformly to its container,
so give the sticky wrapper a bounded height (the `min()` above) rather than a
free one.

`activeId` is yours to compute. An `IntersectionObserver` over the station
`id`s is enough; the rail itself is not a control and adds no tab stops.

### 2. `ChronoRail`

```tsx
<ChronoRail
  stations={STATIONS}          // ChronoStation[]  drawn to true scale
  ghosts={GHOSTS}              // ChronoGhost[]    in the KG, not on the page
  arcs={ARCS}                  // ChronoArc[]      attested reuse, backwards
  activeId={activeId}
  orientation="vertical"       // or "horizontal"
/>
```

`ChronoStation` needs a `year` (negative for BCE) and a `yearLabel`, which the
page's `Thinker` does not carry. Map it once:

```ts
const STATIONS: ChronoStation[] = THINKERS.map((t) => ({
  id: t.id,
  label: t.nav,
  year: WORK_YEAR[t.id],        // date of the WORK, not the life
  yearLabel: WORK_YEAR_LABEL[t.id],
  tone: t.tone,
}));

const ARCS: ChronoArc[] = THINKERS.flatMap((t) =>
  (t.inheritsFrom ?? []).map((navLabel) => ({
    from: t.id,
    to: THINKERS.find((x) => x.nav === navLabel)!.id,
  })),
);
```

Date the **work**, not the life. Marks placed by lifespan put Origen before
Alexander and lie about who could have read whom.

The longest interval between two consecutive stations is computed, cut out of
the rail as a real break in the line, and labelled. Nothing is hardcoded: pass
the eight approved figures and it names the 263 years between Carneades and
Epictetus; pass the old five and it names the 450 between Chrysippus and
Alexander. Ghosts falling inside that interval are what stands in it.

The vertical variant is one uniformly scaled SVG. The horizontal variant draws
only vertical lines and scales anisotropically with `preserveAspectRatio="none"`,
so tick positions stay exact at any width; its labels are real HTML underneath
at a fixed size, which is the only reason it is legible on a phone.

Both variants are `aria-hidden` with a full `sr-only` textual equivalent that
reads out the stations, the interval, its share of the span, the ghosts inside
it and the reuse arcs. That is a better screen-reader experience than eleven
focusable dots, and it keeps eleven tab stops out of the reading order.

### 3. `ThinkerStation`

```tsx
<ThinkerStation
  thinker={thinker}                 // ThinkerLike (your Thinker satisfies it)
  locus={locusStateFor(thinker.id)} // LocusState
  onRetryLocus={() => refetch(thinker.id)}
  description={<p>{kgNode.description}</p>}   // optional, apparatus not lede
  stickyTopClass="top-16"           // where the sticky header parks
/>
```

`stickyTopClass` must clear the site nav. Pass a real Tailwind class; a runtime
value would need an inline `style`.

Order in the main column is stance, then the locus, then `contested`. Evidence
before apparatus, on every breakpoint. `contested` sits in the main column and
is marked by the sage rule, because on this page it is the thesis and not a
footnote. `opponent`, `inheritsFrom`, the KG description and the one outbound
text link live in the right-hand aside.

`thinker.passageRef` and `thinker.passageNote` are merged into the locus, so
the apparatus renders once, above and below the text where it belongs. Do not
also put them in `Locus.reference` / `Locus.note`; the thinker record wins.

`coda: true` (Boethius) drops the aside, narrows the measure and puts a
hairline above the station. It is also the switch that keeps the dry lines out
of that section.

### 4. `BilingualLocus`

Used by `ThinkerStation`, exported for anywhere else a locus is shown.

```tsx
type LocusState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'empty' }
  | { status: 'ready'; locus: Locus };
```

`empty` and `error` are different states and must stay different: one means the
corpus answered and had nothing, the other means it did not answer. Only
`error` gets a retry.

Rules the component enforces, and which the page must not undo:

- the original is never truncated, at any length, for any layout reason;
- `lang="grc"` / `lang="la"` on the original, `lang="en"` on the translation;
- `font-garamond` on both halves. Instrument Serif ships no Greek at all, so
  putting the display face anywhere near a Greek run drops it into Georgia
  mid-sentence;
- Greek leads at 1.85 and measures 48ch, Latin at 1.72 and 52ch;
- the CTS URN is the one monospace element on the page, and it is `select-all`.

**One thing worth knowing before you ship Latin.** EB Garamond ships an
OpenType `locl` feature for Latin, on by default the moment a run carries
`lang="la"`: it substitutes u with v, so Perseus' *igitur* renders as *igitvr*
and Cicero's *volubilitas* as *volvbilitas*. That is a defensible epigraphic
convention and it is not what the edition prints. `EDITION_ORTHOGRAPHY.la` in
`tone.ts` turns it off, `lang="la"` is kept for screen readers and hyphenation,
and a test locks it. Apply that class anywhere else you set Latin.

Text comes from the corpus. Nothing in this folder ships ancient text, and
nothing in it should.

### 5. `CylinderAndSphere`

```tsx
<CylinderAndSphere />   // all copy has defaults; every string is a prop
```

Chrysippus answers the charge that fate makes assent empty with a cylinder: the
push starts it, but it rolls by its own shape, and the shape is its own.
Alexander answers with a sphere on a slope: if a thing's nature settles what it
does, "up to us" has been explained away rather than explained.

Both bodies take the same push. The cylinder decelerates and stops inside its
frame; the sphere accelerates and leaves. A reader who watches once has the
disagreement before reading a caption. Under `prefers-reduced-motion` it is a
strobe photograph, ghosted start and solid end with the travel measured by a
dashed rule, which is arguably the clearer figure of the two.

**Verify before shipping**, since these are the only ancient words the folder
carries and they are only there as defaults:

| String | Where it is claimed to come from |
| --- | --- |
| `volubilitas` | Cicero, *De fato* 43 |
| `σφαίρᾳ` | Alexander, *De fato*, Bruns 185.21, quoted in the header of `theDebateCorpus.ts` |

Pass `cylinder={{...}}` / `sphere={{...}}` with `word: undefined` to drop them.
The heading default, "The same image, turned against its author", states
Alexander's move; it is a prop, so re-word it if you want the attribution more
explicit.

Place it once, between the Chrysippus and Alexander stations. It is the
editorial centrepiece and repeating the device would spend it.

### 6. `ContestedField`

```tsx
<ContestedField questions={QUESTIONS} />
```

Each `ContestedQuestion` carries two or three attributed positions. They are
laid out either side of a hairline with a visible gap where a join would be,
and the gap is never closed. `scholarId` drives cross-highlighting: choose a
name and it lights up on every question it appears on, with a live count. That
is the cross-cutting claim rendered as something the reader can verify instead
of being told.

Highlighting is additive. Nothing dims, so no text drops below its contrast
floor to serve an interaction.

Deliberately **not** a scatter plot. Nobody has published coordinates for these
scholars, so axes would be invented and the figure would look more
authoritative than the evidence behind it.

Four positions on one question is a literature review, not a figure. Split it.

### 7. `DebateOutro`

```tsx
<DebateOutro rail={<ChronoRail stations={STATIONS} ghosts={GHOSTS}
                               orientation="horizontal" />} />
```

Pass the rail with no `activeId`: the whole field at once, silence included,
still open. Heading, body and the dry line are props.

---

## The humour, so you can cut it

Four beats, all removable, none on a primary text and none on anyone's death.

| Where | Line |
| --- | --- |
| Locus loading | "Fetching the passage. It has waited seventeen centuries and can manage another moment." |
| Simile, the sphere | "Out of the frame, and still going. Nothing about it could have done otherwise." |
| Simile, second push | "Same push. Same outcome. That is rather the objection." |
| Outro | "If you were expecting a conclusion, so were they." |

The Boethius coda has none, and `coda: true` is what keeps it that way. The
empty locus state is dry but not a joke, because a missing passage is a real
gap in the corpus: "The argument survives. The file does not, or not here."

---

## Accessibility notes worth keeping

- No component adds a tab stop that is not a real control. The rail adds none.
- `role="status"` with `aria-live="polite"` on loading, empty, error, the
  second-push line, and the cross-highlight count.
- Every focusable element has a visible `focus-visible` ring with an offset
  against the parchment ground.
- Every hover affordance has a focus equivalent; nothing is pointer-only.
- No content is hover-only. The ghosts on the rail, the scholars' claims and
  the attributions are all always visible.
- `motion-reduce:transition-none` on every CSS transition; framer-motion is
  covered by the page-level `MotionConfig reducedMotion="user"`, and
  `CylinderAndSphere` additionally branches its whole figure on
  `useReducedMotion()` rather than merely freezing it.

---

## Tests

```bash
npx vitest run src/components/the-debate
```

`chronology.test.ts` fixes the eight work dates and asserts the things the
design rests on: that the intervals are not equal, that Alexander and Origen
sit inside five per cent of the rail, that the largest silence is 263 years and
resolves to 450 on the old five-figure set, and that Cicero is the only figure
standing in it. `BilingualLocus.test.tsx` locks the `lang` attributes, the
no-truncation rule, the `locl` override and the three async states.
