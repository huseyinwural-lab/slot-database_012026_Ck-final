import React from 'react';
import { AlertCircle, ServerCrash, CreditCard, ShieldAlert } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const CriticalAlertsPanel = ({ alerts }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'provider_failure': return <ServerCrash className="h-4 w-4" />;
      case 'payment_gateway': return <CreditCard className="h-4 w-4" />;
      case 'fraud_engine': return <ShieldAlert className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  return (
    <Card className="border-red-200 bg-red-50/10">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          🔔 Critical Alerts
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No active alerts</p>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 p-2 rounded-md bg-white border shadow-sm">
                <div className={`p-2 rounded-full ${getSeverityColor(alert.severity)} bg-opacity-20`}>
                  {getIcon(alert.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold">{alert.type.replace('_', ' ').toUpperCase()}</span>
                    <Badge variant="outline" className={`text-xs ${getSeverityColor(alert.severity)}`}>
                      {alert.severity}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{alert.message}</p>
                  <p className="text-[10px] text-gray-400 mt-1">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default CriticalAlertsPanel;
