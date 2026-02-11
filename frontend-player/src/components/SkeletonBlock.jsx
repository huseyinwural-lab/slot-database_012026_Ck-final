export const SkeletonBlock = ({ className = '' }) => (
  <div className={`animate-pulse rounded-lg bg-white/10 ${className}`} data-testid="skeleton-block" />
);
