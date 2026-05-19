import {
  BookOpen,
  Brain,
  GraduationCap,
  Landmark,
  Layers,
  MessageSquare,
  Quote,
  Scale,
  ScrollText,
  Sparkles,
  User,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { LayerKind } from '../AtlasHelpers';

interface NodeTypeIconProps {
  readonly typeKey: string;
  readonly layer: LayerKind;
  readonly size?: 'md' | 'sm';
}

const TYPE_ICON: Record<string, LucideIcon> = {
  person: User,
  scholar: GraduationCap,
  concept: Brain,
  argument: Scale,
  work: BookOpen,
  school: Landmark,
  passage: Quote,
  debate: MessageSquare,
  publication: ScrollText,
  reformulation: Layers,
  event: Sparkles,
};

const TYPE_TINT: Record<string, string> = {
  person: 'bg-amber-100/80 text-amber-900 border-amber-300/70',
  scholar: 'bg-teal-100/80 text-teal-900 border-teal-300/60',
  concept: 'bg-sky-100/80 text-sky-900 border-sky-300/70',
  argument: 'bg-violet-100/80 text-violet-900 border-violet-300/70',
  work: 'bg-yellow-100/80 text-yellow-900 border-yellow-300/70',
  school: 'bg-orange-100/80 text-orange-900 border-orange-300/70',
  passage: 'bg-stone-100/80 text-stone-900 border-stone-300/70',
  debate: 'bg-fuchsia-100/80 text-fuchsia-900 border-fuchsia-300/70',
  publication: 'bg-cyan-100/80 text-cyan-900 border-cyan-300/60',
  reformulation: 'bg-indigo-100/80 text-indigo-900 border-indigo-300/60',
  event: 'bg-rose-100/80 text-rose-900 border-rose-300/60',
};

const FALLBACK_TINT = 'bg-stone-100/80 text-stone-800 border-stone-300/70';

export default function NodeTypeIcon({ typeKey, layer, size = 'md' }: NodeTypeIconProps) {
  const effective = layer === 'modern' && typeKey === 'person' ? 'scholar' : typeKey;
  const Icon = TYPE_ICON[effective] ?? (layer === 'modern' ? GraduationCap : Sparkles);
  const tint = TYPE_TINT[effective] ?? FALLBACK_TINT;
  const dim =
    size === 'md'
      ? 'h-12 w-12 rounded-2xl'
      : 'h-7 w-7 rounded-lg';
  const iconDim = size === 'md' ? 'h-6 w-6' : 'h-3.5 w-3.5';

  return (
    <span
      aria-hidden
      className={[
        'inline-flex shrink-0 items-center justify-center border',
        dim,
        tint,
      ].join(' ')}
    >
      <Icon className={iconDim} strokeWidth={1.6} />
    </span>
  );
}
