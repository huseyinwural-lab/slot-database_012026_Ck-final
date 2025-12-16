import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const LossLeadersTable = ({ data }) => {
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-red-600">🎯 Top Negative Performing Games (Loss Leaders)</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Game</TableHead>
              <TableHead>GGR Impact</TableHead>
              <TableHead>RTP</TableHead>
              <TableHead>Provider</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((game, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-medium">{game.game}</TableCell>
                <TableCell className="text-red-600 font-bold">
                  -${Math.abs(game.ggr_impact).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge variant={game.rtp_anomaly > 100 ? "destructive" : "secondary"}>
                    {game.rtp_anomaly}%
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{game.provider}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default LossLeadersTable;
