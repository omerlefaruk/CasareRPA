import { useState, useEffect } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

interface HeaderProps {
  title: string;
  subtitle?: string;
  showSearch?: boolean;
  connectionStatus?: ConnectionStatus;
  className?: string;
}

const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const statusConfig: Record<ConnectionStatus, { color: string; label: string; pulse: boolean }> = {
  connected: {
    color: 'var(--status-completed)',
    label: 'Connected',
    pulse: false,
  },
  connecting: {
    color: 'var(--status-busy)',
    label: 'Connecting',
    pulse: true,
  },
  disconnected: {
    color: 'var(--status-offline)',
    label: 'Disconnected',
    pulse: false,
  },
};

export function Header({
  title,
  subtitle,
  showSearch = false,
  connectionStatus = 'connected',
  className = '',
}: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const headerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 'var(--spacing-md) var(--spacing-xl)',
    backgroundColor: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border-subtle)',
    minHeight: '64px',
  };

  const titleContainerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xs)',
  };

  const titleStyles: CSSProperties = {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: 600,
    color: 'var(--text-primary)',
  };

  const subtitleStyles: CSSProperties = {
    margin: 0,
    fontSize: '0.875rem',
    color: 'var(--text-muted)',
  };

  const actionsContainerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-lg)',
  };

  const searchContainerStyles: CSSProperties = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  };

  const searchInputStyles: CSSProperties = {
    width: '280px',
    padding: 'var(--spacing-sm) var(--spacing-md)',
    paddingLeft: '40px',
    backgroundColor: 'var(--bg-tertiary)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: '0.875rem',
    outline: 'none',
    transition: 'all var(--transition-fast)',
  };

  const searchIconStyles: CSSProperties = {
    position: 'absolute',
    left: '12px',
    color: 'var(--text-muted)',
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
  };

  const statusContainerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-md)',
    padding: 'var(--spacing-sm) var(--spacing-md)',
    backgroundColor: 'var(--bg-tertiary)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-subtle)',
  };

  const statusTextStyles: CSSProperties = {
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
  };

  const timeStyles: CSSProperties = {
    fontSize: '0.875rem',
    color: 'var(--text-muted)',
    fontVariantNumeric: 'tabular-nums',
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <motion.header
      className={className}
      style={headerStyles}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div style={titleContainerStyles}>
        <h1 style={titleStyles}>{title}</h1>
        {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
      </div>

      <div style={actionsContainerStyles}>
        {showSearch && (
          <div style={searchContainerStyles}>
            <span style={searchIconStyles}>
              <SearchIcon />
            </span>
            <input
              type="text"
              placeholder="Search workflows, robots..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={searchInputStyles}
              onFocus={(e) => {
                e.target.style.borderColor = 'var(--border-focus)';
                e.target.style.boxShadow = '0 0 0 2px rgba(99, 102, 241, 0.2)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'var(--border-default)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={timeStyles}>{formatTime(currentTime)}</span>
          <span style={{ ...timeStyles, fontSize: '0.75rem' }}>{formatDate(currentTime)}</span>
        </div>

        <div style={statusContainerStyles}>
          <ConnectionStatusIndicator status={connectionStatus} />
          <span style={statusTextStyles}>{statusConfig[connectionStatus].label}</span>
        </div>
      </div>
    </motion.header>
  );
}

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
}

function ConnectionStatusIndicator({ status }: ConnectionStatusIndicatorProps) {
  const config = statusConfig[status];

  const dotStyles: CSSProperties = {
    width: '8px',
    height: '8px',
    borderRadius: 'var(--radius-full)',
    backgroundColor: config.color,
    position: 'relative',
  };

  if (config.pulse) {
    return (
      <span style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <motion.span
          style={{
            ...dotStyles,
            position: 'absolute',
          }}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [1, 0.5, 1],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <span style={dotStyles} />
      </span>
    );
  }

  return <span style={dotStyles} />;
}

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface HeaderWithBreadcrumbsProps extends HeaderProps {
  breadcrumbs?: BreadcrumbItem[];
}

export function HeaderWithBreadcrumbs({
  breadcrumbs = [],
  ...headerProps
}: HeaderWithBreadcrumbsProps) {
  const breadcrumbContainerStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-sm)',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    marginBottom: 'var(--spacing-xs)',
  };

  const breadcrumbLinkStyles: CSSProperties = {
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'color var(--transition-fast)',
  };

  const breadcrumbSeparatorStyles: CSSProperties = {
    color: 'var(--text-muted)',
  };

  const subtitle = breadcrumbs.length > 0 ? (
    <div style={breadcrumbContainerStyles}>
      {breadcrumbs.map((item, index) => (
        <span key={index} style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          {item.path ? (
            <a
              href={item.path}
              style={breadcrumbLinkStyles}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--text-primary)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              {item.label}
            </a>
          ) : (
            <span style={{ color: 'var(--text-primary)' }}>{item.label}</span>
          )}
          {index < breadcrumbs.length - 1 && (
            <span style={breadcrumbSeparatorStyles}>/</span>
          )}
        </span>
      ))}
    </div>
  ) : undefined;

  return <Header {...headerProps} subtitle={headerProps.subtitle || (subtitle as unknown as string)} />;
}
