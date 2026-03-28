interface BookProgressProps {
  currentPage: number;
  totalPages: number;
  currentRef?: string;
}

export function BookProgress({ currentPage, totalPages, currentRef }: BookProgressProps) {
  const percentage = totalPages > 0 ? Math.round((currentPage / totalPages) * 100) : 0;

  return (
    <div className="w-full max-w-[920px] mx-auto mb-10">
      <div className="h-0.5 bg-white/[0.06] rounded-sm overflow-hidden mb-1.5">
        <div
          className="h-full bg-gradient-to-r from-amber-600 to-amber-700 rounded-sm transition-[width] duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] opacity-35">
        <span>{currentRef ?? ''}</span>
        <span>
          Pages {currentPage}–{Math.min(currentPage + 1, totalPages)} / {totalPages}
        </span>
        <span>{percentage} %</span>
      </div>
    </div>
  );
}
