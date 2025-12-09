import React from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { CRM } from './CRM';

const GenericList = ({ title, endpoint, columns, actions }) => {
// ... (existing GenericList implementation)
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await api.get(endpoint);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [endpoint]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
        {actions && actions.header}
      </div>
      <Card>
        <CardHeader><CardTitle>All Items</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((col, i) => <TableHead key={i}>{col.header}</TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={columns.length} className="text-center">Loading...</TableCell></TableRow>
              ) : data.length === 0 ? (
                <TableRow><TableCell colSpan={columns.length} className="text-center">No records found</TableCell></TableRow>
              ) : data.map((item, i) => (
                <TableRow key={i}>
                  {columns.map((col, j) => (
                    <TableCell key={j}>
                      {col.render ? col.render(item) : item[col.accessor]}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export const KYC = () => {
  const handleReview = async (id, status) => {
    try { await api.post(`/v1/kyc/documents/${id}/review`, { status }); toast.success(`Document ${status}`); }
    catch { toast.error("Failed"); }
  };
  return <GenericList 
    title="KYC Verification" 
    endpoint="/v1/kyc/queue" 
    columns={[
      { header: "User", accessor: "player_username" },
      { header: "Type", accessor: "type" },
      { header: "Status", render: (d) => <Badge variant={d.status==='approved'?'default':d.status==='rejected'?'destructive':'secondary'}>{d.status}</Badge> },
      { header: "Actions", render: (d) => d.status === 'pending' && (
        <div className="flex gap-2">
            <Button size="sm" onClick={()=>handleReview(d.id, 'approved')}>Approve</Button>
            <Button size="sm" variant="destructive" onClick={()=>handleReview(d.id, 'rejected')}>Reject</Button>
        </div>
      )}
    ]}
  />;
};

// Export the new CRM component
export { CRM };

export const CMS = () => <GenericList title="Content Management" endpoint="/v1/cms/banners" columns={[
  { header: "Title", accessor: "title" }, { header: "Position", accessor: "position" }, { header: "Active", render: d => d.active ? "Yes" : "No" }
]} />;

export const Affiliates = () => <GenericList title="Affiliate Management" endpoint="/v1/affiliates" columns={[
  { header: "Partner", accessor: "name" }, { header: "Commission", render: d => `${d.commission_rate*100}%` }, { header: "Earnings", render: d => `$${d.total_earnings}` }
]} />;

export const Risk = () => <GenericList title="Risk Management Rules" endpoint="/v1/risk/rules" columns={[
  { header: "Rule Name", accessor: "name" }, { header: "Condition", accessor: "condition" }, { header: "Action", accessor: "action" }, { header: "Severity", render: d=> <Badge variant="outline">{d.severity}</Badge> }
]} />;

export const Admins = () => <GenericList title="Admin Users" endpoint="/v1/admin/users" columns={[
  { header: "Username", accessor: "username" }, { header: "Role", accessor: "role" }, { header: "Email", accessor: "email" }
]} />;

export const Logs = () => <GenericList title="System Logs" endpoint="/v1/logs/system" columns={[
  { header: "Time", render: d => new Date(d.timestamp).toLocaleString() }, { header: "Service", accessor: "service" }, { header: "Level", render: d => <Badge>{d.level}</Badge> }, { header: "Message", accessor: "message" }
]} />;

export const RG = () => <GenericList title="Responsible Gaming" endpoint="/v1/rg/limits" columns={[
  { header: "Player ID", accessor: "player_id" }, { header: "Type", accessor: "type" }, { header: "Amount", accessor: "amount" }, { header: "Period", accessor: "period" }
]} />;

export const Reports = () => (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
        <div className="grid md:grid-cols-2 gap-6">
            <Card><CardHeader><CardTitle>Financial Report</CardTitle></CardHeader><CardContent className="h-40 flex items-center justify-center bg-secondary/20">Chart Placeholder</CardContent></Card>
            <Card><CardHeader><CardTitle>Player Retention</CardTitle></CardHeader><CardContent className="h-40 flex items-center justify-center bg-secondary/20">Chart Placeholder</CardContent></Card>
        </div>
    </div>
);
