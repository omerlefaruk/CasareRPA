import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';

type SkeletonVariant = 'text' | 'circular' | 'rectangular';

interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  count?: number;
  className?: string;
  style?: CSSProperties;
}

const variantStyles: Record<SkeletonVariant, CSSProperties> = {
  text: {
    borderRadius: 'var(--radius-sm)',
    height: '1em',
  },
  circular: {
    borderRadius: 'var(--radius-full)',
  },
  rectangular: {
    borderRadius: 'var(--radius-md)',
  },
};

function SkeletonItem({
  variant = 'text',
  width,
  height,
  className = '',
  style,
}: Omit<SkeletonProps, 'count'>) {
  const baseStyles: CSSProperties = {
    display: 'block',
    backgroundColor: 'var(--bg-tertiary)',
    backgroundImage: 'linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-hover) 50%, var(--bg-tertiary) 100%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s ease-in-out infinite',
    width: typeof width === 'number' ? `${width}px` : width || '100%',
    height: typeof height === 'number' ? `${height}px` : height,
    ...variantStyles[variant],
    ...style,
  };

  if (variant === 'circular') {
    const size = width || height || 40;
    baseStyles.width = typeof size === 'number' ? `${size}px` : size;
    baseStyles.height = typeof size === 'number' ? `${size}px` : size;
  }

  return (
    <motion.span
      className={className}
      style={baseStyles}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.15 }}
      aria-hidden="true"
    />
  );
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  count = 1,
  className = '',
  style,
}: SkeletonProps) {
  if (count === 1) {
    return (
      <SkeletonItem
        variant={variant}
        width={width}
        height={height}
        className={className}
        style={style}
      />
    );
  }

  const containerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-sm)',
  };

  return (
    <div style={containerStyles} className={className}>
      {Array.from({ length: count }, (_, index) => (
        <SkeletonItem
          key={index}
          variant={variant}
          width={width}
          height={height}
          style={style}
        />
      ))}
    </div>
  );
}

interface SkeletonCardProps {
  lines?: number;
  showAvatar?: boolean;
  className?: string;
}

export function SkeletonCard({ lines = 3, showAvatar = false, className = '' }: SkeletonCardProps) {
  const cardStyles: CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-md)',
  };

  const headerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-md)',
    marginBottom: 'var(--spacing-md)',
  };

  const contentStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-sm)',
  };

  return (
    <div style={cardStyles} className={className}>
      <div style={headerStyles}>
        {showAvatar && <Skeleton variant="circular" width={40} height={40} />}
        <div style={{ flex: 1 }}>
          <Skeleton variant="text" width="60%" height={16} />
          <Skeleton variant="text" width="40%" height={12} style={{ marginTop: 'var(--spacing-xs)' }} />
        </div>
      </div>
      <div style={contentStyles}>
        {Array.from({ length: lines }, (_, index) => (
          <Skeleton
            key={index}
            variant="text"
            width={index === lines - 1 ? '75%' : '100%'}
            height={14}
          />
        ))}
      </div>
    </div>
  );
}

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function SkeletonTable({ rows = 5, columns = 4, className = '' }: SkeletonTableProps) {
  const tableStyles: CSSProperties = {
    width: '100%',
    borderCollapse: 'collapse',
  };

  const cellStyles: CSSProperties = {
    padding: 'var(--spacing-md)',
    borderBottom: '1px solid var(--border-subtle)',
  };

  const headerCellStyles: CSSProperties = {
    ...cellStyles,
    backgroundColor: 'var(--bg-tertiary)',
  };

  return (
    <table style={tableStyles} className={className}>
      <thead>
        <tr>
          {Array.from({ length: columns }, (_, index) => (
            <th key={index} style={headerCellStyles}>
              <Skeleton variant="text" height={14} width="70%" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }, (_, rowIndex) => (
          <tr key={rowIndex}>
            {Array.from({ length: columns }, (_, colIndex) => (
              <td key={colIndex} style={cellStyles}>
                <Skeleton variant="text" height={14} width={colIndex === 0 ? '80%' : '60%'} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
