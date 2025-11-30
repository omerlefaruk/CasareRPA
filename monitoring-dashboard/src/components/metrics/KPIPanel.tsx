/**
 * KPIPanel - Row of 4 critical KPI cards for the monitoring dashboard.
 *
 * Displays: Total Robots, Active Jobs, Success Rate, Queue Depth
 * with live indicators, sparklines, and conditional styling.
 */

import { useMemo } from 'react';
import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { KPICard } from '../ui/KPICard';

// ============================================================================
// Types
// ============================================================================

export interface KPIPanelProps {
  totalRobots: number;
  activeRobots?: number;
  activeJobs: number;
  successRate: number;
  queueDepth: number;
  sparklineData?: number[];
  isLoading?: boolean;
}

// ============================================================================
// SVG Icons
// ============================================================================

/**
 * Server/Computer icon for Total Robots
 */
function ServerIcon({ color = 'currentColor', size = 24 }: { color?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
      <circle cx="6" cy="6" r="1" fill={color} stroke="none" />
      <circle cx="6" cy="18" r="1" fill={color} stroke="none" />
      <line x1="10" y1="6" x2="18" y2="6" />
      <line x1="10" y1="18" x2="18" y2="18" />
    </svg>
  );
}

/**
 * Play Circle icon for Active Jobs
 */
function PlayCircleIcon({ color = 'currentColor', size = 24 }: { color?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <polygon points="10,8 16,12 10,16" fill={color} stroke="none" />
    </svg>
  );
}

/**
 * Check Circle icon for Success Rate
 */
function CheckCircleIcon({ color = 'currentColor', size = 24 }: { color?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

/**
 * Layers/Stack icon for Queue Depth
 */
function LayersIcon({ color = 'currentColor', size = 24 }: { color?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="12,2 2,7 12,12 22,7" />
      <polyline points="2,17 12,22 22,17" />
      <polyline points="2,12 12,17 22,12" />
    </svg>
  );
}

// ============================================================================
// Loading Skeleton
// ============================================================================

function KPICardSkeleton({ index }: { index: number }) {
  const skeletonStyles: CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--spacing-lg)',
    position: 'relative',
    overflow: 'hidden',
    minHeight: 140,
  };

  const shimmerStyles: CSSProperties = {
    background: `linear-gradient(
      90deg,
      var(--bg-tertiary) 0%,
      var(--bg-hover) 50%,
      var(--bg-tertiary) 100%
    )`,
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: 'var(--radius-sm)',
  };

  return (
    <motion.div
      style={skeletonStyles}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      {/* Title skeleton */}
      <div style={{ ...shimmerStyles, width: '60%', height: 12, marginBottom: 'var(--spacing-md)' }} />
      {/* Value skeleton */}
      <div style={{ ...shimmerStyles, width: '40%', height: 40, marginBottom: 'var(--spacing-sm)' }} />
      {/* Footer skeleton */}
      <div style={{ ...shimmerStyles, width: '30%', height: 10 }} />
    </motion.div>
  );
}

// ============================================================================
// Animation Variants
// ============================================================================

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 24,
    },
  },
};

// ============================================================================
// Accent Colors
// ============================================================================

const ACCENT_COLORS = {
  robots: '#3b82f6',      // Blue
  activeJobs: '#f97316',  // Orange
  successRate: '#22c55e', // Green
  queueNormal: '#eab308', // Yellow
  queueHigh: '#ef4444',   // Red (when > 10)
} as const;

// ============================================================================
// Component
// ============================================================================

export function KPIPanel({
  totalRobots,
  activeRobots,
  activeJobs,
  successRate,
  queueDepth,
  sparklineData,
  isLoading = false,
}: KPIPanelProps) {
  // Determine queue accent color based on depth
  const queueAccentColor = useMemo(() => {
    return queueDepth > 10 ? ACCENT_COLORS.queueHigh : ACCENT_COLORS.queueNormal;
  }, [queueDepth]);

  // Generate subtitle for robots card
  const robotsSubtitle = useMemo(() => {
    if (activeRobots !== undefined) {
      return `${activeRobots} active`;
    }
    return undefined;
  }, [activeRobots]);

  // Container styles - responsive grid
  const containerStyles: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 'var(--spacing-lg)',
    width: '100%',
  };

  // Wrapper for each card to apply stagger animation
  const cardWrapperStyles: CSSProperties = {
    minWidth: 0, // Prevent grid blowout
  };

  if (isLoading) {
    return (
      <motion.div
        style={containerStyles}
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        {[0, 1, 2, 3].map((index) => (
          <KPICardSkeleton key={index} index={index} />
        ))}
      </motion.div>
    );
  }

  return (
    <motion.div
      style={containerStyles}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="kpi-panel"
    >
      {/* Total Robots */}
      <motion.div style={cardWrapperStyles} variants={itemVariants}>
        <KPICard
          title="Total Robots"
          value={totalRobots}
          format="number"
          icon={<ServerIcon color={ACCENT_COLORS.robots} size={20} />}
          accentColor={ACCENT_COLORS.robots}
          suffix={robotsSubtitle ? `(${robotsSubtitle})` : undefined}
        />
      </motion.div>

      {/* Active Jobs */}
      <motion.div style={cardWrapperStyles} variants={itemVariants}>
        <KPICard
          title="Active Jobs"
          value={activeJobs}
          format="number"
          icon={<PlayCircleIcon color={ACCENT_COLORS.activeJobs} size={20} />}
          accentColor={ACCENT_COLORS.activeJobs}
          isLive={activeJobs > 0}
        />
      </motion.div>

      {/* Success Rate */}
      <motion.div style={cardWrapperStyles} variants={itemVariants}>
        <KPICard
          title="Success Rate"
          value={successRate}
          format="percentage"
          icon={<CheckCircleIcon color={ACCENT_COLORS.successRate} size={20} />}
          accentColor={ACCENT_COLORS.successRate}
          sparklineData={sparklineData}
        />
      </motion.div>

      {/* Queue Depth */}
      <motion.div style={cardWrapperStyles} variants={itemVariants}>
        <KPICard
          title="Queue Depth"
          value={queueDepth}
          format="number"
          icon={<LayersIcon color={queueAccentColor} size={20} />}
          accentColor={queueAccentColor}
          isLive={queueDepth > 10}
        />
      </motion.div>
    </motion.div>
  );
}

// ============================================================================
// Responsive Styles Component
// ============================================================================

/**
 * Injects responsive CSS for KPIPanel grid.
 * Call once at app level or include in component.
 */
const RESPONSIVE_STYLES = `
  .kpi-panel {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 1200px) {
    .kpi-panel {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 600px) {
    .kpi-panel {
      grid-template-columns: 1fr;
    }
  }
`;

/**
 * Component that injects responsive styles.
 * Include once in your app or layout.
 */
export function KPIPanelStyles() {
  return <style>{RESPONSIVE_STYLES}</style>;
}

export default KPIPanel;
