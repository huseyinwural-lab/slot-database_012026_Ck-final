import React, { useEffect, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '../../services/api';

const GameConfigReadOnlyPanel = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [snapshot, setSnapshot] = useState(null);

  useEffect(() => {
    if (!game?.id) return;

    const run = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/v1/games/${game.id}/config`);
        setSnapshot(res.data);
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [game?.id]);

  return (
    <div className="space-y-4">
      <Alert>
        <AlertDescription>
          This configuration is read-only in this environment. Editing and publishing are disabled.
        </AlertDescription>
      </Alert>

      <div className="flex items-center gap-2">
        <Badge variant="secondary">read-only</Badge>
        {snapshot?.status && <Badge variant="outline">{snapshot.status}</Badge>}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {loading && <div className="text-muted-foreground">Loading…</div>}

          {!loading && snapshot && (
            <div className="space-y-2">
              <div><span className="text-muted-foreground">Game ID:</span> {snapshot.game_id}</div>
              <div><span className="text-muted-foreground">Name:</span> {snapshot.name}</div>
              <div><span className="text-muted-foreground">Provider:</span> {snapshot.provider}</div>
              <div><span className="text-muted-foreground">Category:</span> {snapshot.category}</div>
              <div><span className="text-muted-foreground">RTP:</span> {snapshot.rtp == null ? '-' : snapshot.rtp}</div>
              <div><span className="text-muted-foreground">Volatility:</span> {snapshot.volatility == null ? '-' : String(snapshot.volatility)}</div>
              <div><span className="text-muted-foreground">Limits:</span> {snapshot.limits == null ? '-' : JSON.stringify(snapshot.limits)}</div>
              <div><span className="text-muted-foreground">Features:</span> {(snapshot.features || []).length ? (snapshot.features || []).join(', ') : '-'}</div>
            </div>
          )}

          {!loading && !snapshot && (
            <div className="text-muted-foreground">No snapshot available.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default GameConfigReadOnlyPanel;
