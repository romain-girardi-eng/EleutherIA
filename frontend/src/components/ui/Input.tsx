import React, { forwardRef, useState } from 'react';
import type { InputHTMLAttributes } from 'react';
import { cn } from '../../utils/cn';
import { X, Eye, EyeOff, Search, AlertCircle, Check } from 'lucide-react';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Label text for the input */
  label?: string;
  /** Error message to display */
  error?: string;
  /** Hint or helper text */
  hint?: string;
  /** Icon to display on the left side */
  leftIcon?: React.ReactNode;
  /** Icon to display on the right side */
  rightIcon?: React.ReactNode;
  /** Whether to show clear button when input has value */
  showClear?: boolean;
  /** Callback when clear button is clicked */
  onClear?: () => void;
  /** Whether the input should take full width */
  fullWidth?: boolean;
  /** Size variant of the input */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Whether to show success state */
  success?: boolean;
  /** Whether to show character count */
  showCount?: boolean;
  /** Maximum character count to display */
  maxCount?: number;
}

/**
 * Input component with validation and various states
 *
 * @example
 * <Input
 *   label="Email"
 *   type="email"
 *   placeholder="Enter your email"
 *   error="Invalid email address"
 *   showClear
 * />
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      showClear = false,
      onClear,
      fullWidth = false,
      type,
      value,
      disabled,
      size = 'md',
      success,
      showCount = false,
      maxCount,
      maxLength,
      id,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';
    const actualType = isPassword && showPassword ? 'text' : type;
    const hasValue = value !== undefined && value !== null && String(value).length > 0;

    const sizeClasses = {
      xs: 'h-7 px-2 text-xs',
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-3 text-base',
      lg: 'h-12 px-4 text-lg',
      xl: 'h-14 px-4 text-xl',
    };

    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    const currentLength = value ? String(value).length : 0;
    const effectiveMaxLength = maxLength || maxCount;

    return (
      <div className={cn('space-y-2', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'block font-medium',
              size === 'xs' || size === 'sm' ? 'text-sm' : 'text-base',
              error && 'text-red-600',
              success && 'text-green-600',
              !error && !success && 'text-academic-text'
            )}
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className={cn(
              'absolute left-3 top-1/2 -translate-y-1/2',
              error ? 'text-red-500' :
              success ? 'text-green-500' :
              'text-academic-muted'
            )}>
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            type={actualType}
            value={value}
            disabled={disabled}
            maxLength={effectiveMaxLength}
            className={cn(
              'w-full border rounded-md transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              sizeClasses[size],
              error
                ? 'border-red-500 focus:ring-red-500 focus:border-red-500 text-red-900 placeholder-red-300'
                : success
                ? 'border-green-500 focus:ring-green-500 focus:border-green-500 text-green-900'
                : 'border-academic-border hover:border-primary-400 focus:ring-primary-600 focus:border-transparent',
              leftIcon && 'pl-10',
              (showClear && hasValue) || isPassword || rightIcon || showCount ?
                size === 'xs' || size === 'sm' ? 'pr-8' : 'pr-10'
                : '',
              className
            )}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` :
              hint ? `${inputId}-hint` :
              undefined
            }
            {...props}
          />

          {/* Right side icons/buttons */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
            {/* Character count */}
            {showCount && effectiveMaxLength && (
              <span className={cn(
                'text-xs',
                currentLength > effectiveMaxLength ? 'text-red-500' :
                currentLength > effectiveMaxLength * 0.9 ? 'text-amber-500' :
                'text-gray-400'
              )}>
                {currentLength}/{effectiveMaxLength}
              </span>
            )}

            {/* Success icon */}
            {success && !error && !showClear && !isPassword && (
              <Check className="h-4 w-4 text-green-500" />
            )}

            {/* Clear button */}
            {showClear && hasValue && !disabled && (
              <button
                type="button"
                onClick={onClear}
                className="text-academic-muted hover:text-academic-text transition-colors"
                aria-label="Clear input"
              >
                <X className="h-4 w-4" />
              </button>
            )}

            {/* Password toggle */}
            {isPassword && (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-academic-muted hover:text-academic-text transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            )}

            {/* Custom right icon */}
            {!showClear && !isPassword && !success && rightIcon && (
              <div className="text-academic-muted">
                {rightIcon}
              </div>
            )}
          </div>

          {/* Error icon */}
          {error && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500">
              <AlertCircle className="h-4 w-4" />
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-red-600 flex items-center gap-1" role="alert">
            <AlertCircle className="h-3 w-3" />
            {error}
          </p>
        )}

        {/* Hint/helper text */}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="text-sm text-academic-muted">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };

/**
 * Specialized Input Components
 */

export interface SearchInputProps extends Omit<InputProps, 'leftIcon' | 'type'> {
  onSearch?: (value: string) => void;
}

/**
 * SearchInput - Pre-configured input for search functionality
 */
export function SearchInput({
  onSearch,
  onClear,
  className,
  ...props
}: SearchInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSearch) {
      onSearch(e.currentTarget.value);
    }
  };

  return (
    <Input
      type="search"
      leftIcon={<Search className="h-4 w-4" />}
      showClear
      onClear={onClear}
      onKeyDown={handleKeyDown}
      placeholder="Search..."
      className={className}
      {...props}
    />
  );
}

export interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  fullWidth?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showCount?: boolean;
  maxCount?: number;
}

/**
 * Textarea component with validation
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      label,
      error,
      hint,
      fullWidth = false,
      size = 'md',
      showCount = false,
      maxCount,
      maxLength,
      value,
      id,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: 'p-2 text-sm',
      md: 'p-3 text-base',
      lg: 'p-4 text-lg',
    };

    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const currentLength = value ? String(value).length : 0;
    const effectiveMaxLength = maxLength || maxCount;

    return (
      <div className={cn('space-y-2', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={textareaId}
            className={cn(
              'block font-medium',
              size === 'sm' ? 'text-sm' : 'text-base',
              error ? 'text-red-600' : 'text-academic-text'
            )}
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          <textarea
            ref={ref}
            id={textareaId}
            value={value}
            maxLength={effectiveMaxLength}
            className={cn(
              'w-full border rounded-md transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              'resize-y min-h-[100px]',
              sizeClasses[size],
              error
                ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                : 'border-academic-border hover:border-primary-400 focus:ring-primary-600 focus:border-transparent',
              className
            )}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${textareaId}-error` :
              hint ? `${textareaId}-hint` :
              undefined
            }
            {...props}
          />

          {showCount && effectiveMaxLength && (
            <div className="absolute bottom-2 right-2">
              <span className={cn(
                'text-xs',
                currentLength > effectiveMaxLength ? 'text-red-500' :
                currentLength > effectiveMaxLength * 0.9 ? 'text-amber-500' :
                'text-gray-400'
              )}>
                {currentLength}/{effectiveMaxLength}
              </span>
            </div>
          )}
        </div>

        {error && (
          <p id={`${textareaId}-error`} className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}

        {hint && !error && (
          <p id={`${textareaId}-hint`} className="text-sm text-academic-muted">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

/**
 * FormField wrapper for consistent form layouts
 */
interface FormFieldProps {
  children: React.ReactNode;
  className?: string;
}

export function FormField({ children, className }: FormFieldProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {children}
    </div>
  );
}

/**
 * FormGroup for grouping related form fields
 */
interface FormGroupProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}

export function FormGroup({ children, className, title, description }: FormGroupProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {(title || description) && (
        <div className="space-y-1">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {description && <p className="text-sm text-academic-muted">{description}</p>}
        </div>
      )}
      {children}
    </div>
  );
}
