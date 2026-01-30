import React from 'react';
import { cn } from '../../utils/cn';
import { cva, type VariantProps } from 'class-variance-authority';

const cardVariants = cva(
  'bg-white rounded-lg transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'border border-academic-border',
        elevated: 'shadow-lg hover:shadow-xl',
        outlined: 'border-2 border-primary-200',
        ghost: 'hover:bg-gray-50',
        gradient: 'bg-gradient-to-br from-primary-50 to-primary-100 border border-primary-200',
      },
      padding: {
        none: '',
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
        xl: 'p-8',
      },
      interactive: {
        true: 'cursor-pointer hover:shadow-md active:shadow-sm transform hover:-translate-y-0.5 active:translate-y-0',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'md',
      interactive: false,
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  /** Whether the card should have hover effects on the entire card */
  hoverable?: boolean;
}

/**
 * Card component for content containers
 *
 * @example
 * <Card variant="elevated" padding="lg">
 *   <CardHeader>
 *     <CardTitle>Title</CardTitle>
 *     <CardDescription>Description</CardDescription>
 *   </CardHeader>
 *   <CardContent>Content here</CardContent>
 *   <CardFooter>Footer actions</CardFooter>
 * </Card>
 */
const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, interactive, hoverable, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          cardVariants({ variant, padding, interactive: interactive || hoverable }),
          className
        )}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

// Card sub-components
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether to add padding to the header */
  noPadding?: boolean;
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, noPadding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex flex-col space-y-1.5',
        !noPadding && 'p-6 pb-0',
        className
      )}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /** HTML element to render as */
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, as: Component = 'h3', ...props }, ref) => {
    return (
      <Component
        ref={ref}
        className={cn(
          'text-xl font-semibold leading-none tracking-tight',
          className
        )}
        {...props}
      />
    );
  }
);
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-academic-muted', className)}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether to add padding to the content */
  noPadding?: boolean;
}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, noPadding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(!noPadding && 'p-6 pt-4', className)}
      {...props}
    />
  )
);
CardContent.displayName = 'CardContent';

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether to add padding to the footer */
  noPadding?: boolean;
  /** Alignment of footer content */
  align?: 'left' | 'center' | 'right' | 'between';
}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, noPadding, align = 'left', ...props }, ref) => {
    const alignmentClasses = {
      left: 'justify-start',
      center: 'justify-center',
      right: 'justify-end',
      between: 'justify-between',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center',
          alignmentClasses[align],
          !noPadding && 'p-6 pt-0',
          className
        )}
        {...props}
      />
    );
  }
);
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };

/**
 * Specialized card components
 */

export interface MetricCardProps extends Omit<CardProps, 'children'> {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string | number;
    direction: 'up' | 'down' | 'neutral';
  };
  className?: string;
}

/**
 * MetricCard - Specialized card for displaying metrics/KPIs
 */
export function MetricCard({
  title,
  value,
  description,
  icon,
  trend,
  className,
  ...cardProps
}: MetricCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <Card className={className} {...cardProps}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-primary-600">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div className={cn('flex items-center text-xs mt-2', trendColors[trend.direction])}>
            <span className="mr-1">{trendIcons[trend.direction]}</span>
            <span>{trend.value}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export interface FeatureCardProps extends Omit<CardProps, 'children'> {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  badge?: string;
  className?: string;
}

/**
 * FeatureCard - Specialized card for displaying features
 */
export function FeatureCard({
  icon,
  title,
  description,
  action,
  badge,
  className,
  ...cardProps
}: FeatureCardProps) {
  return (
    <Card
      className={className}
      interactive={!!action}
      {...cardProps}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            {icon && (
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center text-primary-600">
                {icon}
              </div>
            )}
            <div>
              <CardTitle className="flex items-center gap-2">
                {title}
                {badge && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                    {badge}
                  </span>
                )}
              </CardTitle>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-sm">{description}</CardDescription>
      </CardContent>
      {action && (
        <CardFooter>
          {action}
        </CardFooter>
      )}
    </Card>
  );
}

export interface SimpleCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title for the card */
  title?: string;
  /** Subtitle or description */
  subtitle?: string;
  /** Content padding size */
  padding?: 'sm' | 'md' | 'lg';
  /** Whether to show a border */
  bordered?: boolean;
  /** Whether to show shadow */
  shadow?: boolean;
}

/**
 * SimpleCard - A simpler card variant for basic content
 */
export function SimpleCard({
  title,
  subtitle,
  children,
  className,
  padding = 'md',
  bordered = true,
  shadow = false,
  ...props
}: SimpleCardProps) {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg',
        bordered && 'border border-gray-200',
        shadow && 'shadow-md',
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}
