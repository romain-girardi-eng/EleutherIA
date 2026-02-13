import React, { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

const buttonVariants = cva(
  // Base styles that apply to all buttons
  'inline-flex items-center justify-center font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-95',
  {
    variants: {
      variant: {
        primary:
          'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-600 shadow-sm hover:shadow-md',
        secondary:
          'bg-primary-100 text-primary-900 hover:bg-primary-200 focus-visible:ring-primary-600',
        outline:
          'border border-academic-border bg-transparent hover:bg-academic-hover focus-visible:ring-primary-600',
        ghost:
          'hover:bg-academic-hover hover:text-primary-900 focus-visible:ring-primary-600',
        danger:
          'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-600 shadow-sm hover:shadow-md',
        destructive:
          'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-600 shadow-sm hover:shadow-md',
        link:
          'text-primary-600 underline-offset-4 hover:underline focus-visible:ring-primary-600 p-0 h-auto',
        success:
          'bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-600 shadow-sm hover:shadow-md',
        warning:
          'bg-amber-600 text-white hover:bg-amber-700 focus-visible:ring-amber-600 shadow-sm hover:shadow-md',
        default:
          'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-600 shadow-sm hover:shadow-md',
      },
      size: {
        xs: 'h-7 px-2 text-xs rounded',
        sm: 'h-8 px-3 text-sm rounded-md',
        md: 'h-10 px-4 text-base rounded-md',
        default: 'h-10 px-4 text-base rounded-md',
        lg: 'h-12 px-6 text-lg rounded-lg',
        xl: 'h-14 px-8 text-xl rounded-lg',
        icon: 'h-10 w-10 rounded-md', // Square icon button
        'icon-sm': 'h-8 w-8 rounded-md',
        'icon-xs': 'h-6 w-6 rounded',
      },
      fullWidth: {
        true: 'w-full',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'default',
      fullWidth: false,
    },
  }
);

export interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'color'>,
    VariantProps<typeof buttonVariants> {
  /** Use Radix Slot for composable components */
  asChild?: boolean;
  /** Show loading spinner and disable interaction */
  loading?: boolean;
  /** Icon to display on the left side */
  leftIcon?: React.ReactNode;
  /** Icon to display on the right side */
  rightIcon?: React.ReactNode;
  /** Loading text to display (defaults to children) */
  loadingText?: string;
  /** Whether to show a subtle pulse animation */
  pulse?: boolean;
  /** Custom spinner icon */
  spinner?: React.ReactNode;
}

/**
 * Button component with multiple variants and states
 *
 * @example
 * // Primary button with loading state
 * <Button loading={isLoading}>Save Changes</Button>
 *
 * @example
 * // Button with icon
 * <Button leftIcon={<Search />}>Search</Button>
 *
 * @example
 * // Danger button full width
 * <Button variant="danger" fullWidth>Delete Account</Button>
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      loading = false,
      leftIcon,
      rightIcon,
      loadingText,
      pulse = false,
      spinner,
      children,
      disabled,
      asChild = false,
      ...props
    },
    ref
  ) => {
    // Use Radix Slot if asChild is true
    const Comp = asChild ? Slot : 'button';

    // Don't show text for icon-only sizes when loading
    const isIconOnly = size === 'icon' || size === 'icon-sm' || size === 'icon-xs';
    const showLoadingText = !isIconOnly && loadingText;

    // Loading spinner component
    const loadingSpinner = spinner || (
      <Loader2
        className={cn(
          'animate-spin',
          isIconOnly ? 'h-4 w-4' : 'h-4 w-4 mr-2'
        )}
        aria-label="Loading"
      />
    );

    return (
      <Comp
        className={cn(
          buttonVariants({ variant, size, fullWidth }),
          pulse && !disabled && 'animate-pulse',
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        aria-disabled={disabled || loading}
        {...props}
      >
        {/* Loading state */}
        {loading ? (
          <>
            {loadingSpinner}
            {showLoadingText && (
              <span className="inline-block">{loadingText}</span>
            )}
            {!showLoadingText && !isIconOnly && children}
            {loading && <span className="sr-only">Loading...</span>}
          </>
        ) : (
          <>
            {/* Left icon */}
            {leftIcon && (
              <span className={cn(
                'inline-flex shrink-0',
                !isIconOnly && children && 'mr-2'
              )}>
                {leftIcon}
              </span>
            )}

            {/* Children content */}
            {children}

            {/* Right icon */}
            {rightIcon && (
              <span className={cn(
                'inline-flex shrink-0',
                !isIconOnly && children && 'ml-2'
              )}>
                {rightIcon}
              </span>
            )}
          </>
        )}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

// eslint-disable-next-line react-refresh/only-export-components
export { Button, buttonVariants };

/**
 * Button Group component for grouping related actions
 */
export interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
  size?: 'sm' | 'md' | 'lg';
}

export function ButtonGroup({
  children,
  className,
  orientation = 'horizontal',
  size = 'md'
}: ButtonGroupProps) {
  const groupClasses = cn(
    'inline-flex',
    orientation === 'horizontal' ? 'flex-row' : 'flex-col',
    className
  );

  // Add connected styling for button children
  const childrenWithProps = React.Children.map(children, (child, index) => {
    if (React.isValidElement(child)) {
      const isFirst = index === 0;
      const isLast = index === React.Children.count(children) - 1;

      return React.cloneElement(child as React.ReactElement<{ className?: string; size?: string }>, {
        className: cn(
          (child as React.ReactElement<{ className?: string }>).props.className,
          orientation === 'horizontal' ? [
            !isFirst && '-ml-px',
            !isFirst && !isLast && 'rounded-none',
            isFirst && 'rounded-r-none',
            isLast && 'rounded-l-none',
          ] : [
            !isFirst && '-mt-px',
            !isFirst && !isLast && 'rounded-none',
            isFirst && 'rounded-b-none',
            isLast && 'rounded-t-none',
          ]
        ),
        size: (child as React.ReactElement<{ size?: string }>).props.size || size,
      });
    }
    return child;
  });

  return (
    <div className={groupClasses} role="group">
      {childrenWithProps}
    </div>
  );
}
