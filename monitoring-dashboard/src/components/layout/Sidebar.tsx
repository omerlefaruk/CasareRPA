import { useState } from 'react';
import type { CSSProperties } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

const DashboardIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);

const FleetIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="6" width="20" height="12" rx="2" />
    <path d="M12 12h.01" />
    <path d="M17 12h.01" />
    <path d="M7 12h.01" />
  </svg>
);

const JobsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    <path d="M9 14l2 2 4-4" />
  </svg>
);

const SchedulesIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const AnalyticsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const CollapseIcon = ({ collapsed }: { collapsed: boolean }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform var(--transition-normal)' }}
  >
    <polyline points="15 18 9 12 15 6" />
  </svg>
);

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/fleet', label: 'Fleet', icon: <FleetIcon /> },
  { path: '/jobs', label: 'Jobs', icon: <JobsIcon /> },
  { path: '/schedules', label: 'Schedules', icon: <SchedulesIcon /> },
  { path: '/analytics', label: 'Analytics', icon: <AnalyticsIcon /> },
];

export function Sidebar({ collapsed: controlledCollapsed, onToggleCollapse, className = '' }: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);

  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const handleToggle = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  const sidebarStyles: CSSProperties = {
    width: isCollapsed ? '64px' : '240px',
    height: '100vh',
    backgroundColor: 'var(--bg-secondary)',
    borderRight: '1px solid var(--border-subtle)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'width var(--transition-normal)',
    position: 'relative',
    flexShrink: 0,
  };

  const logoContainerStyles: CSSProperties = {
    padding: 'var(--spacing-lg)',
    borderBottom: '1px solid var(--border-subtle)',
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-md)',
    minHeight: '64px',
  };

  const logoStyles: CSSProperties = {
    width: '32px',
    height: '32px',
    backgroundColor: 'var(--accent-primary)',
    borderRadius: 'var(--radius-md)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--text-primary)',
    fontWeight: 700,
    fontSize: '14px',
    flexShrink: 0,
  };

  const navContainerStyles: CSSProperties = {
    flex: 1,
    padding: 'var(--spacing-md)',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xs)',
    overflowY: 'auto',
    overflowX: 'hidden',
  };

  const collapseButtonStyles: CSSProperties = {
    position: 'absolute',
    right: '-12px',
    top: '72px',
    width: '24px',
    height: '24px',
    backgroundColor: 'var(--bg-tertiary)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-full)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    color: 'var(--text-secondary)',
    zIndex: 10,
  };

  return (
    <motion.aside
      className={className}
      style={sidebarStyles}
      initial={false}
      animate={{ width: isCollapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
    >
      <div style={logoContainerStyles}>
        <div style={logoStyles}>CR</div>
        <AnimatePresence>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{
                fontWeight: 600,
                fontSize: '1rem',
                color: 'var(--text-primary)',
                whiteSpace: 'nowrap',
              }}
            >
              CasareRPA
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      <nav style={navContainerStyles}>
        {navItems.map((item) => (
          <SidebarNavItem
            key={item.path}
            item={item}
            collapsed={isCollapsed}
          />
        ))}
      </nav>

      <button
        onClick={handleToggle}
        style={collapseButtonStyles}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <CollapseIcon collapsed={isCollapsed} />
      </button>
    </motion.aside>
  );
}

interface SidebarNavItemProps {
  item: NavItem;
  collapsed: boolean;
}

function SidebarNavItem({ item, collapsed }: SidebarNavItemProps) {
  const baseLinkStyles: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-md)',
    padding: collapsed ? 'var(--spacing-sm)' : 'var(--spacing-sm) var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'all var(--transition-fast)',
    justifyContent: collapsed ? 'center' : 'flex-start',
    position: 'relative',
    overflow: 'hidden',
  };

  const activeLinkStyles: CSSProperties = {
    ...baseLinkStyles,
    backgroundColor: 'var(--accent-primary)',
    color: 'var(--text-primary)',
  };

  const hoverStyles: CSSProperties = {
    backgroundColor: 'var(--bg-hover)',
    color: 'var(--text-primary)',
  };

  return (
    <NavLink
      to={item.path}
      style={({ isActive }) => (isActive ? activeLinkStyles : baseLinkStyles)}
      onMouseEnter={(e) => {
        const target = e.currentTarget;
        if (!target.classList.contains('active')) {
          Object.assign(target.style, hoverStyles);
        }
      }}
      onMouseLeave={(e) => {
        const target = e.currentTarget;
        if (!target.classList.contains('active')) {
          target.style.backgroundColor = 'transparent';
          target.style.color = 'var(--text-secondary)';
        }
      }}
      title={collapsed ? item.label : undefined}
    >
      <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
        {item.icon}
      </span>
      <AnimatePresence>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              fontSize: '0.875rem',
              fontWeight: 500,
              whiteSpace: 'nowrap',
            }}
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>
    </NavLink>
  );
}
