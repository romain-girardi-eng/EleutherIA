interface BookHeaderProps {
  leftText: string;
  rightText: string;
}

export function BookHeader({ leftText, rightText }: BookHeaderProps) {
  return (
    <div className="flex justify-between font-garamond text-[10px] tracking-[2px] uppercase text-stone-400 mb-7 pb-2 border-b border-stone-900/[0.08]">
      <span>{leftText}</span>
      <span>{rightText}</span>
    </div>
  );
}
