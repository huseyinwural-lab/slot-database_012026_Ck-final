import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Gift, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

const BonusPerformanceCard = ({ data }) => {
  return (
    <Card className="col-span-12 md:col-span-4">
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Gift className="h-4 w-4 text-purple-500" /> Bonus Performance
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Given Today</div>
            <div className="text-lg font-bold">{data.given_count}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Redeemed</div>
            <div className="text-lg font-bold text-blue-600">{data.redeemed_count}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Total Value</div>
            <div className="text-lg font-bold text-yellow-600">${data.total_value.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Expired</div>
            <div className="text-lg font-bold text-gray-500">{data.expired_count}</div>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t space-y-3">
          <div className="flex justify-between items-center text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <TrendingUp className="h-3 w-3" /> Bonus ROI
            </span>
            <span className={data.roi >= 0 ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
              {data.roi}%
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <CheckCircle className="h-3 w-3" /> Wagering Completion
            </span>
            <span className="font-bold">{data.wagering_completion_rate}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default BonusPerformanceCard;
