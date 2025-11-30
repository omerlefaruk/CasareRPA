import { useRef, useMemo, useCallback } from 'react';
import type { CSSProperties } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { RobotCard } from './RobotCard';
import type { RobotSummary } from './RobotCard';

interface RobotGridProps {
  robots: RobotSummary[];
  onRobotClick?: (robot: RobotSummary) => void;
  selectedRobotId?: string | null;
  columnCount?: number;
  rowHeight?: number;
  gap?: number;
}

const CARD_MIN_HEIGHT = 220;
const DEFAULT_GAP = 16;
const DEFAULT_COLUMNS = 4;

export function RobotGrid({
  robots,
  onRobotClick,
  selectedRobotId = null,
  columnCount = DEFAULT_COLUMNS,
  rowHeight = CARD_MIN_HEIGHT,
  gap = DEFAULT_GAP,
}: RobotGridProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowCount = useMemo(() => {
    return Math.ceil(robots.length / columnCount);
  }, [robots.length, columnCount]);

  const getRowRobots = useCallback((rowIndex: number): RobotSummary[] => {
    const startIndex = rowIndex * columnCount;
    const endIndex = Math.min(startIndex + columnCount, robots.length);
    return robots.slice(startIndex, endIndex);
  }, [robots, columnCount]);

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight + gap,
    overscan: 3,
  });

  const virtualRows = virtualizer.getVirtualItems();

  const containerStyles: CSSProperties = {
    height: '100%',
    minHeight: 400,
    maxHeight: 'calc(100vh - 300px)',
    overflow: 'auto',
    contain: 'strict',
  };

  const innerContainerStyles: CSSProperties = {
    height: `${virtualizer.getTotalSize()}px`,
    width: '100%',
    position: 'relative',
  };

  const rowStyles = useCallback((start: number): CSSProperties => ({
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: rowHeight,
    transform: `translateY(${start}px)`,
    display: 'grid',
    gridTemplateColumns: `repeat(${columnCount}, 1fr)`,
    gap: gap,
  }), [columnCount, gap, rowHeight]);

  const emptyStateStyles: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 'var(--spacing-2xl)',
    color: 'var(--text-muted)',
    textAlign: 'center',
    minHeight: 300,
  };

  const emptyIconStyles: CSSProperties = {
    fontSize: '3rem',
    marginBottom: 'var(--spacing-md)',
    opacity: 0.5,
  };

  if (robots.length === 0) {
    return (
      <div style={emptyStateStyles}>
        <div style={emptyIconStyles}>
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <rect x="3" y="8" width="18" height="12" rx="2" />
            <path d="M7 8V6a2 2 0 012-2h6a2 2 0 012 2v2" />
            <circle cx="9" cy="13" r="1" />
            <circle cx="15" cy="13" r="1" />
            <path d="M9 17h6" />
          </svg>
        </div>
        <p style={{ fontSize: '1rem', fontWeight: 500, marginBottom: 'var(--spacing-xs)' }}>
          No robots available
        </p>
        <p style={{ fontSize: '0.875rem' }}>
          Robots will appear here once they connect to the orchestrator
        </p>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      style={containerStyles}
      role="grid"
      aria-label={`Robot fleet grid with ${robots.length} robots`}
      aria-rowcount={rowCount}
      aria-colcount={columnCount}
    >
      <div style={innerContainerStyles}>
        {virtualRows.map((virtualRow) => {
          const rowRobots = getRowRobots(virtualRow.index);

          return (
            <div
              key={virtualRow.key}
              style={rowStyles(virtualRow.start)}
              role="row"
              aria-rowindex={virtualRow.index + 1}
            >
              {rowRobots.map((robot, colIndex) => (
                <div
                  key={robot.robot_id}
                  role="gridcell"
                  aria-colindex={colIndex + 1}
                >
                  <RobotCard
                    robot={robot}
                    onClick={onRobotClick}
                    isSelected={selectedRobotId === robot.robot_id}
                  />
                </div>
              ))}
              {/* Fill empty cells to maintain grid structure */}
              {rowRobots.length < columnCount &&
                Array.from({ length: columnCount - rowRobots.length }).map((_, i) => (
                  <div
                    key={`empty-${virtualRow.index}-${i}`}
                    role="gridcell"
                    aria-colindex={rowRobots.length + i + 1}
                  />
                ))
              }
            </div>
          );
        })}
      </div>
    </div>
  );
}

export type { RobotGridProps };
export type { RobotSummary };
