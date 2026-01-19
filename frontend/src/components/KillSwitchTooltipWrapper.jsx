import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const KillSwitchTooltipWrapper = ({ disabled, tooltip, children }) => {
  if (!disabled) return children;

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children}
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip || 'Module disabled by Kill Switch'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default KillSwitchTooltipWrapper;
