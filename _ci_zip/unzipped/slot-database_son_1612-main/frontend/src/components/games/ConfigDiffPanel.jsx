import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const changeTypeVariant = (type) => {
  switch (type) {
    case 'added':
      return 'default';
    case 'removed':
      return 'destructive';
    case 'modified':
    default:
      return 'outline';
  }
};

const prettyValue = (v) => {
  if (v === null || v === undefined) return '-';
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return String(v);
  try {
    return JSON.stringify(v);
  } catch (e) {
    return String(v);
  }
};

const ConfigDiffPanel = ({
  open,
  onOpenChange,
  configType,
  fromVersion,
  toVersion,
  changes,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-sm">
            Config Diff – {configType} ({fromVersion?.slice(0, 8)} → {toVersion?.slice(0, 8)})
          </DialogTitle>
        </DialogHeader>
        {(!changes || changes.length === 0) ? (
          <p className="text-xs text-muted-foreground">Bu iki versiyon arasında fark bulunamadı.</p>
        ) : (
          <div className="mt-2 max-h-80 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Old</TableHead>
                  <TableHead>New</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {changes.map((ch, idx) => (
                  <TableRow key={ch.field_path + idx}>
                    <TableCell className="font-mono text-xs max-w-xs truncate">
                      {ch.field_path || '(root)'}
                    </TableCell>
                    <TableCell className="text-xs align-top">{prettyValue(ch.old_value)}</TableCell>
                    <TableCell className="text-xs align-top">{prettyValue(ch.new_value)}</TableCell>
                    <TableCell className="text-xs">
                      <Badge variant={changeTypeVariant(ch.change_type)}>{ch.change_type}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ConfigDiffPanel;
