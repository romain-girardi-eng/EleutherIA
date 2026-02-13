"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../utils/cn"

const gradientButtonVariants = cva(
  [
    "gradient-button",
    "inline-flex items-center justify-center",
    "rounded-[11px] min-w-[132px] px-9 py-4",
    "text-base leading-[19px] font-[500] text-white",
    "font-sans font-bold",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    "transition-all duration-500",
  ],
  {
    variants: {
      variant: {
        default: "",
        academic: "gradient-button-academic",
        stoic: "gradient-button-stoic",
        epicurean: "gradient-button-epicurean",
        highlight: "gradient-button-highlight",
        ultrathink: "gradient-button-ultrathink",
      },
      size: {
        sm: "min-w-[100px] px-6 py-2 text-sm",
        md: "min-w-[132px] px-9 py-4 text-base",
        lg: "min-w-[160px] px-12 py-5 text-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface GradientButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof gradientButtonVariants> {
  asChild?: boolean
  icon?: React.ReactNode
}

const GradientButton = React.forwardRef<HTMLButtonElement, GradientButtonProps>(
  ({ className, variant, size, asChild = false, icon, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(gradientButtonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      >
        {icon && <span className="mr-2">{icon}</span>}
        {children}
      </Comp>
    )
  }
)
GradientButton.displayName = "GradientButton"

// eslint-disable-next-line react-refresh/only-export-components
export { GradientButton, gradientButtonVariants }
