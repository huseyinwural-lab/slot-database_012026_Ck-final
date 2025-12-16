import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Play } from 'lucide-react';

const LiveBetsTicker = ({ bets }) => {
  return (
    <Card className="col-span-12 md:col-span-4 h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Play className="h-4 w-4 text-green-500 fill-current" /> Live Bets Feed
        </CardTitle>
        <Badge variant="outline" className="animate-pulse text-green-600 border-green-200 bg-green-50">LIVE</Badge>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[300px] overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow className="h-8 hover:bg-transparent">
                <TableHead className="h-8 text-xs">Player</TableHead>
                <TableHead className="h-8 text-xs">Game</TableHead>
                <TableHead className="h-8 text-xs text-right">Bet/Win</TableHead>
                <TableHead className="h-8 text-xs text-right">X</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bets.map((bet, idx) => (
                <TableRow key={idx} className="h-10">
                  <TableCell className="py-1 text-xs font-medium truncate max-w-[80px]" title={bet.player_id}>
                    {bet.player_id}
                  </TableCell>
                  <TableCell className="py-1 text-xs truncate max-w-[100px]" title={bet.game}>
                    {bet.game}
                  </TableCell>
                  <TableCell className="py-1 text-xs text-right">
                    <div className="text-muted-foreground">${bet.bet}</div>
                    <div className={bet.win > 0 ? "text-green-600 font-bold" : "text-gray-400"}>
                      ${bet.win}
                    </div>
                  </TableCell>
                  <TableCell className="py-1 text-xs text-right">
                    {bet.multiplier > 0 && (
                      <Badge variant="secondary" className={bet.multiplier >= 10 ? "bg-purple-100 text-purple-700" : ""}>
                        {bet.multiplier}x
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default LiveBetsTicker;
