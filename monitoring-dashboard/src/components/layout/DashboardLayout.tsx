import { useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

interface DashboardLayoutProps {
  children: ReactNode;
  pageTitle: string;
  pageSubtitle?: string;
  showSearch?: boolean;
  connectionStatus?: ConnectionStatus;
  className?: string;
}

export function DashboardLayout({
  children,
  pageTitle,
  pageSubtitle,
  showSearch = true,
  connectionStatus = 'connected',
  className = '',
}: DashboardLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const layoutStyles: CSSProperties = {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: 'var(--bg-primary)',
  };

  const mainContainerStyles: CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
    overflow: 'hidden',
  };

  const contentStyles: CSSProperties = {
    flex: 1,
    padding: 'var(--spacing-xl)',
    overflowY: 'auto',
    overflowX: 'hidden',
  };

  return (
    <div style={layoutStyles} className={className}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div style={mainContainerStyles}>
        <Header
          title={pageTitle}
          subtitle={pageSubtitle}
          showSearch={showSearch}
          connectionStatus={connectionStatus}
        />

        <motion.main
          style={contentStyles}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
}

interface DashboardGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4;
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function DashboardGrid({
  children,
  columns = 3,
  gap = 'lg',
  className = '',
}: DashboardGridProps) {
  const gapMap = {
    sm: 'var(--spacing-sm)',
    md: 'var(--spacing-md)',
    lg: 'var(--spacing-lg)',
  };

  const gridStyles: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: gapMap[gap],
  };

  return (
    <div style={gridStyles} className={className}>
      {children}
    </div>
  );
}

interface DashboardSectionProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function DashboardSection({
  children,
  title,
  subtitle,
  action,
  className = '',
}: DashboardSectionProps) {
  const sectionStyles: CSSProperties = {
    marginBottom: 'var(--spacing-xl)',
  };

  const headerStyles: CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 'var(--spacing-lg)',
  };

  const titleStyles: CSSProperties = {
    margin: 0,
    fontSize: '1.125rem',
    fontWeight: 600,
    color: 'var(--text-primary)',
  };

  const subtitleStyles: CSSProperties = {
    margin: 'var(--spacing-xs) 0 0',
    fontSize: '0.875rem',
    color: 'var(--text-muted)',
  };

  return (
    <motion.section
      style={sectionStyles}
      className={className}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      {(title || action) && (
        <div style={headerStyles}>
          <div>
            {title && <h2 style={titleStyles}>{title}</h2>}
            {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </motion.section>
  );
}

interface DashboardRowProps {
  children: ReactNode;
  gap?: 'sm' | 'md' | 'lg';
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around';
  wrap?: boolean;
  className?: string;
}

export function DashboardRow({
  children,
  gap = 'lg',
  align = 'stretch',
  justify = 'start',
  wrap = false,
  className = '',
}: DashboardRowProps) {
  const gapMap = {
    sm: 'var(--spacing-sm)',
    md: 'var(--spacing-md)',
    lg: 'var(--spacing-lg)',
  };

  const alignMap = {
    start: 'flex-start',
    center: 'center',
    end: 'flex-end',
    stretch: 'stretch',
  };

  const justifyMap = {
    start: 'flex-start',
    center: 'center',
    end: 'flex-end',
    between: 'space-between',
    around: 'space-around',
  };

  const rowStyles: CSSProperties = {
    display: 'flex',
    gap: gapMap[gap],
    alignItems: alignMap[align],
    justifyContent: justifyMap[justify],
    flexWrap: wrap ? 'wrap' : 'nowrap',
  };

  return (
    <div style={rowStyles} className={className}>
      {children}
    </div>
  );
}

interface DashboardColumnProps {
  children: ReactNode;
  flex?: number | string;
  minWidth?: string;
  maxWidth?: string;
  className?: string;
}

export function DashboardColumn({
  children,
  flex = 1,
  minWidth,
  maxWidth,
  className = '',
}: DashboardColumnProps) {
  const columnStyles: CSSProperties = {
    flex: typeof flex === 'number' ? flex : flex,
    minWidth,
    maxWidth,
  };

  return (
    <div style={columnStyles} className={className}>
      {children}
    </div>
  );
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  const containerStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 'var(--spacing-2xl)',
    textAlign: 'center',
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-lg)',
    border: '1px dashed var(--border-default)',
  };

  const iconContainerStyles: CSSProperties = {
    width: '64px',
    height: '64px',
    borderRadius: 'var(--radius-full)',
    backgroundColor: 'var(--bg-tertiary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 'var(--spacing-lg)',
    color: 'var(--text-muted)',
  };

  const titleStyles: CSSProperties = {
    margin: 0,
    fontSize: '1rem',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginBottom: 'var(--spacing-sm)',
  };

  const descriptionStyles: CSSProperties = {
    margin: 0,
    fontSize: '0.875rem',
    color: 'var(--text-muted)',
    maxWidth: '400px',
    marginBottom: action ? 'var(--spacing-lg)' : 0,
  };

  return (
    <motion.div
      style={containerStyles}
      className={className}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
    >
      {icon && <div style={iconContainerStyles}>{icon}</div>}
      <h3 style={titleStyles}>{title}</h3>
      {description && <p style={descriptionStyles}>{description}</p>}
      {action}
    </motion.div>
  );
}
