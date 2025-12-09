import React, { useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const FraudCheck = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const [form, setForm] = useState({
    amount: 5000,
    merchant_name: "Unknown Casino",
    customer_email: "suspicious@user.com",
    ip_address: "192.168.1.1"
  });

  const analyze = async () => {
    setLoading(true);
    try {
        const payload = {
            transaction: {
                transaction_id: `TX-${Date.now()}`,
                amount: Number(form.amount),
                merchant_name: form.merchant_name,
                customer_email: form.customer_email,
                ip_address: form.ip_address,
                timestamp: new Date().toISOString()
            }
        };
        const res = await api.post('/v1/fraud/analyze', payload);
        setResult(res.data);
        toast.success("Analysis Complete");
    } catch (err) {
        toast.error("Analysis Failed");
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">AI Fraud Analysis</h2>
        
        <div className="grid md:grid-cols-2 gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>Manual Transaction Check</CardTitle>
                    <CardDescription>Simulate a transaction to check risk score via OpenAI.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Amount ($)</Label>
                        <Input type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Merchant</Label>
                        <Input value={form.merchant_name} onChange={e => setForm({...form, merchant_name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Customer Email</Label>
                        <Input value={form.customer_email} onChange={e => setForm({...form, customer_email: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>IP Address</Label>
                        <Input value={form.ip_address} onChange={e => setForm({...form, ip_address: e.target.value})} />
                    </div>
                    <Button className="w-full" onClick={analyze} disabled={loading}>
                        {loading ? "Analyzing..." : "Check Risk Score"}
                    </Button>
                </CardContent>
            </Card>

            {result && (
                <Card className={result.is_fraudulent ? "border-red-500 bg-red-950/10" : "border-green-500 bg-green-950/10"}>
                    <CardHeader>
                        <CardTitle>Analysis Result</CardTitle>
                        <div className="text-4xl font-bold mt-2">
                            {(result.fraud_risk_score * 100).toFixed(1)}% Risk
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <span className="font-semibold">Recommendation:</span>
                            <p className="text-lg">{result.recommendations}</p>
                        </div>
                        <div>
                            <span className="font-semibold">Risk Factors:</span>
                            <ul className="list-disc pl-5 mt-1">
                                {result.risk_factors.map((f, i) => <li key={i}>{f}</li>)}
                            </ul>
                        </div>
                        <div className="text-xs text-muted-foreground mt-4">
                            Confidence: {(result.confidence_level * 100).toFixed(0)}%
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    </div>
  );
};

export default FraudCheck;
