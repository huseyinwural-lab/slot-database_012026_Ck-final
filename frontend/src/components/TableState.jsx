import React from 'react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

// Reusable table body helpers to standardize loading/empty/error states.
// Keeps changes minimal by allowing drop-in inside <TableBody>.

export const TableSkeletonRows = ({ colSpan, rows = 6 }) => (
  <>
    {Array.from({ length: rows }).map((_, i) => (
      <tr key={`skeleton-${i}`}>
        <td colSpan={colSpan} className="py-2">
          <Skeleton className="h-8 w-full" />
        </td>
      </tr>
    ))}
  </>
);

export const TableEmptyState = ({ colSpan, title, description, actionLabel, onAction }) => (
  <tr>
    <td colSpan={colSpan}>
      <div className="py-10 text-center">
        <div className="text-sm font-medium">{title}</div>
        {description ? <div className="text-xs text-muted-foreground">{description}</div> : null}
        {actionLabel && onAction ? (
          <div className="mt-3">
            <Button size="sm" variant="outline" onClick={onAction}>
              {actionLabel}
            </Button>
          </div>
        ) : null}
      </div>
    </td>
  </tr>
);

export const TableErrorState = ({ colSpan, title, description, onRetry }) => (
  <tr>
    <td colSpan={colSpan}>
      <div className="py-10 text-center">
        <div className="text-sm font-medium">{title}</div>
        {description ? <div className="text-xs text-muted-foreground">{description}</div> : null}
        {onRetry ? (
          <div className="mt-3">
            <Button size="sm" variant="outline" onClick={onRetry}>
              Tekrar Dene
            </Button>
          </div>
        ) : null}
      </div>
    </td>
  </tr>
);
