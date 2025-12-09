import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const ApprovalQueue = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
        const res = await api.get('/v1/approvals');
        setItems(res.data);
    } catch (err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleAction = async (id, action) => {
    try {
        await api.post(`/v1/approvals/${id}/action`, { action });
        toast.success(`Request ${action}ed`);
        fetchQueue();
    } catch (err) {
        toast.error("Action failed");
    }
  };

  return (
    <div className="space-y-6">
        <div>
            <h2 className="text-3xl font-bold tracking-tight">Approval Queue (4-Eyes)</h2>
            <p className="text-muted-foreground">Review high-risk actions requiring secondary approval.</p>
        </div>

        <div className="grid gap-4">
            {loading && <div>Loading queue...</div>}
            {!loading && items.length === 0 && <div className="p-10 text-center text-muted-foreground border rounded-lg border-dashed">No pending approvals. Good job!</div>}
            
            {items.map(item => (
                <Card key={item.id} className="border-l-4 border-l-yellow-500">
                    <CardHeader className="flex flex-row items-start justify-between pb-2">
                        <div>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                                {item.type.replace('_', ' ').toUpperCase()}
                            </CardTitle>
                            <CardDescription>Requested by {item.requester_admin} at {new Date(item.created_at).toLocaleString()}</CardDescription>
                        </div>
                        <Badge variant="outline" className="text-lg font-bold">${item.amount}</Badge>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between mt-4">
                            <div className="text-sm text-muted-foreground">
                                Related ID: <span className="font-mono text-foreground">{item.related_entity_id}</span>
                            </div>
                            <div className="flex gap-3">
                                <Button variant="outline" className="text-red-500 hover:text-red-600" onClick={() => handleAction(item.id, 'reject')}>
                                    <XCircle className="w-4 h-4 mr-2" /> Reject
                                </Button>
                                <Button className="bg-green-600 hover:bg-green-700" onClick={() => handleAction(item.id, 'approve')}>
                                    <CheckCircle className="w-4 h-4 mr-2" /> Approve
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    </div>
  );
};

export default ApprovalQueue;
