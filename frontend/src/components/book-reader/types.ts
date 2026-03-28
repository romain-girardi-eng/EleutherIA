export interface PageConfig {
  /** Text area width in px (excluding ref margin) */
  width: number;
  /** Text area height in px (excluding header/footer) */
  height: number;
  /** Width of canonical ref margin column in px */
  marginRef: number;
  /** Body font size in px */
  fontSize: number;
  /** Line-height ratio */
  lineHeight: number;
  /** CSS font-family string for Pretext canvas measurement */
  fontFamily: string;
}

export interface PagePassage {
  passageId: string;
  canonicalRef: string;
  /** Full text, or partial if split across pages */
  text: string;
  /** Character offset if passage continues from previous page */
  startOffset?: number;
  /** Character offset if passage continues on next page */
  endOffset?: number;
  /** Number of KG nodes linked to this passage (0 = no icon) */
  kgNodeCount: number;
}

export interface BookPage {
  pageNumber: number;
  passages: PagePassage[];
}

export interface BookSpreadData {
  /** Left page (original language) */
  left: BookPage;
  /** Right page (translation) */
  right: BookPage;
}

export type FontSizePreset = 'small' | 'normal' | 'large';

export const FONT_SIZE_MAP: Record<FontSizePreset, number> = {
  small: 14,
  normal: 17,
  large: 20,
};

export const MOBILE_BREAKPOINT = 900;
