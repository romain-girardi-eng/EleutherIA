import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { BookOpen, Users, Calendar, GraduationCap } from "lucide-react";

interface CitationPreviewProps {
  children: React.ReactNode;
  citation: string;
  type: "ancient" | "modern";
  className?: string;
  nodeInfo?: {
    label?: string;
    period?: string;
    school?: string;
    description?: string;
  };
}

export const CitationPreview = ({
  children,
  citation,
  type,
  className,
  nodeInfo,
}: CitationPreviewProps) => {
  const [isOpen, setOpen] = React.useState(false);

  return (
    <HoverCardPrimitive.Root
      openDelay={300}
      closeDelay={100}
      onOpenChange={(open) => {
        setOpen(open);
      }}
    >
      <HoverCardPrimitive.Trigger
        className={cn(
          "cursor-help border-b-2 border-dotted transition-colors",
          type === "ancient"
            ? "border-blue-400 hover:border-blue-600 text-blue-700 hover:text-blue-900"
            : "border-green-400 hover:border-green-600 text-green-700 hover:text-green-900",
          className
        )}
        asChild
      >
        <span>{children}</span>
      </HoverCardPrimitive.Trigger>

      <HoverCardPrimitive.Content
        className="[transform-origin:var(--radix-hover-card-content-transform-origin)] z-50"
        side="top"
        align="center"
        sideOffset={8}
      >
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
                transition: {
                  type: "spring",
                  stiffness: 300,
                  damping: 25,
                },
              }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className={cn(
                "max-w-sm rounded-lg shadow-lg border-2 p-3 bg-white",
                type === "ancient"
                  ? "border-blue-200 bg-blue-50"
                  : "border-green-200 bg-green-50"
              )}
            >
              {/* Header with icon */}
              <div className="flex items-start gap-2 mb-2">
                {type === "ancient" ? (
                  <BookOpen className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <Users className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-semibold text-gray-700 mb-1">
                    {type === "ancient" ? "Ancient Source" : "Modern Scholarship"}
                  </h4>
                </div>
              </div>

              {/* Node info if available */}
              {nodeInfo && (
                <div className="mb-2 pb-2 border-b border-gray-200">
                  {nodeInfo.label && (
                    <p className="text-sm font-semibold text-gray-900 mb-1">
                      {nodeInfo.label}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {nodeInfo.period && (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-white rounded-full border border-gray-200">
                        <Calendar className="w-3 h-3" />
                        {nodeInfo.period}
                      </span>
                    )}
                    {nodeInfo.school && (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-white rounded-full border border-gray-200">
                        <GraduationCap className="w-3 h-3" />
                        {nodeInfo.school}
                      </span>
                    )}
                  </div>
                  {nodeInfo.description && (
                    <p className="text-xs text-gray-600 mt-1.5 line-clamp-2">
                      {nodeInfo.description}
                    </p>
                  )}
                </div>
              )}

              {/* Citation text */}
              <div className="text-xs text-gray-700 leading-relaxed">
                <p className="font-serif italic">{citation}</p>
              </div>

              {/* Footer hint */}
              <div className="mt-2 pt-2 border-t border-gray-200">
                <p className="text-xs text-gray-500 italic">
                  Click on nodes above to view full details
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </HoverCardPrimitive.Content>
    </HoverCardPrimitive.Root>
  );
};
