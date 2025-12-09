import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserPlus, TrendingUp, Calendar } from 'lucide-react';

const FTDCard = ({ data }) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">💼 First Time Deposits (FTD)</CardTitle>
        <UserPlus className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm text-muted-foreground">Today</span>
            </div>
            <span className="text-2xl font-bold">{data.ftd_today}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-muted-foreground">This Month</span>
            </div>
            <span className="font-bold">{data.ftd_month.toLocaleString()}</span>
          </div>
          <div className="pt-2">
            <div className="text-xs text-muted-foreground mb-1">Conversion (Reg → FTD)</div>
            <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
              <div 
                className="bg-primary h-full transition-all duration-500" 
                style={{ width: `${data.conversion_rate}%` }}
              />
            </div>
            <div className="text-right text-xs font-medium mt-1">{data.conversion_rate}%</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default FTDCard;
