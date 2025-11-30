import type { ReactNode, CSSProperties } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';

interface CardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  children: ReactNode;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  className?: string;
  style?: CSSProperties;
}

const paddingMap = {
  none: '0',
  sm: 'var(--spacing-sm)',
  md: 'var(--spacing-md)',
  lg: 'var(--spacing-lg)',
};

const variantStyles: Record<string, CSSProperties> = {
  default: {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
  },
  elevated: {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-default)',
    boxShadow: 'var(--shadow-card)',
  },
  outlined: {
    backgroundColor: 'transparent',
    border: '1px solid var(--border-default)',
  },
};

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  style,
  ...motionProps
}: CardProps) {
  const baseStyles: CSSProperties = {
    borderRadius: 'var(--radius-lg)',
    padding: paddingMap[padding],
    transition: 'all var(--transition-normal)',
    ...variantStyles[variant],
    ...style,
  };

  return (
    <motion.div
      className={className}
      style={baseStyles}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      {...motionProps}
    >
      {children}
    </motion.div>
  );
}

// Card Header component
interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, action, className = '' }: CardHeaderProps) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 'var(--spacing-md)',
      }}
    >
      <div>
        <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {title}
        </h3>
        {subtitle && (
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            {subtitle}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

// Card Content component
interface CardContentProps {
  children: ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
  return <div className={className}>{children}</div>;
}
