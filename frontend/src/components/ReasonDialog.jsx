import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';

const ReasonDialog = ({ open, onOpenChange, title, placeholder, confirmText = 'Confirm', onConfirm }) => {
  const [reason, setReason] = useState('');
  const [touched, setTouched] = useState(false);

  const canSubmit = reason.trim().length > 0;

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        onOpenChange(nextOpen);
        if (!nextOpen) {
          setReason('');
          setTouched(false);
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            {/* Use Input for maximum Playwright selector compatibility */}
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              onBlur={() => setTouched(true)}
              placeholder={placeholder || 'Enter audit reason...'}
              data-testid="reason-input"
            />
            {touched && !canSubmit && (
              <div className="text-sm text-destructive mt-1">Reason cannot be empty</div>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button
              onClick={() => onConfirm(reason.trim())}
              disabled={!canSubmit}
              data-testid="reason-confirm"
            >
              {confirmText}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ReasonDialog;
