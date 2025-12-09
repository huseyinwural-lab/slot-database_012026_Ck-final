import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const FinancialTrendChart = ({ data }) => {
  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>🔥 Deposits & Withdrawals Trend (30 Days)</CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="date" 
              tickLine={false} 
              axisLine={false} 
              tickMargin={8}
              tickFormatter={(value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            />
            <YAxis 
              tickLine={false} 
              axisLine={false} 
              tickFormatter={(value) => `$${value/1000}k`}
            />
            <Tooltip 
              formatter={(value) => [`$${value.toLocaleString()}`, "Amount"]}
              labelFormatter={(label) => new Date(label).toLocaleDateString()}
            />
            <Legend />
            <Line type="monotone" dataKey="deposits" stroke="#10b981" strokeWidth={2} dot={false} name="Deposits" />
            <Line type="monotone" dataKey="withdrawals" stroke="#ef4444" strokeWidth={2} dot={false} name="Withdrawals" />
            <Line type="monotone" dataKey="net_cashflow" stroke="#3b82f6" strokeWidth={2} dot={false} name="Net Cashflow" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default FinancialTrendChart;
