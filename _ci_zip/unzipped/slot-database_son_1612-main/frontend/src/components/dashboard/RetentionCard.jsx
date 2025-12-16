import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Users, UserMinus, UserCheck } from 'lucide-react';

const RetentionCard = ({ data }) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">📈 Retention & Churn</CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-muted-foreground">1-Day Retention</span>
            </div>
            <span className="font-bold">{data.retention_1d}%</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-green-500" />
              <span className="text-sm text-muted-foreground">7-Day Retention</span>
            </div>
            <span className="font-bold">{data.retention_7d}%</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserMinus className="h-4 w-4 text-red-500" />
              <span className="text-sm text-muted-foreground">Churn Rate</span>
            </div>
            <span className="font-bold text-red-600">{data.churn_rate}%</span>
          </div>
          <div className="pt-2 border-t text-xs text-muted-foreground text-center">
            {data.returning_players.toLocaleString()} returning players this week
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default RetentionCard;
