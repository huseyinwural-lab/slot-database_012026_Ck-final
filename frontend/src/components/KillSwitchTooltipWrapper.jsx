import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const KillSwitchTooltipWrapper = ({ disabled, tooltip, children }) => {
  if (!disabled) return children;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="opacity-50 cursor-not-allowed">
            <div className="pointer-events-none">{children}</div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip || 'Module disabled by Kill Switch'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default KillSwitchTooltipWrapper;
