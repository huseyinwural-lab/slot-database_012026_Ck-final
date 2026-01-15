import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { FileCode, Eye, Upload } from 'lucide-react';
import api from '../services/api';

const MathAssetsPage = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [uploadOpen, setUploadOpen] = useState(false);
  
  const [form, setForm] = useState({ ref_key: '', type: 'paytable', content_json: '' });

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const res = await api.get('/v1/math-assets', { params: { search, type: typeFilter } });
      setAssets(res.data.items || []);
    } catch (e) {
      toast.error('Failed to load assets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [search, typeFilter]);

  const handleUpload = async () => {
    try {
      let content;
      try {
        content = JSON.parse(form.content_json);
      } catch {
        toast.error('Invalid JSON content');
        return;
      }

      await api.post('/v1/math-assets', {
        ref_key: form.ref_key,
        type: form.type,
        content: content,
        reason: 'Admin UI math asset upload'
      });
      
      setUploadOpen(false);
      setForm({ ref_key: '', type: 'paytable', content_json: '' });
      fetchAssets();
      toast.success('Asset Uploaded');
    } catch (e) {
      toast.error(e?.response?.data?.detail?.message || e?.response?.data?.detail || 'Upload failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <FileCode className="w-8 h-8" /> Math Assets
        </h2>
        
        <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
          <DialogTrigger asChild>
            <Button>
              <Upload className="w-4 h-4 mr-2" /> Upload New Asset
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Upload Math Asset</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Reference Key (Unique ID)</Label>
                <Input 
                  value={form.ref_key} 
                  onChange={e => setForm({...form, ref_key: e.target.value})} 
                  placeholder="e.g., basic_pay_v2" 
                />
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={form.type} onValueChange={v => setForm({...form, type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="paytable">Paytable</SelectItem>
                    <SelectItem value="reelset">Reelset</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>JSON Content</Label>
                <Textarea 
                  value={form.content_json} 
                  onChange={e => setForm({...form, content_json: e.target.value})}
                  className="font-mono text-xs h-64"
                  placeholder="{ ... }"
                />
              </div>
              <Button onClick={handleUpload} className="w-full">Upload</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4">
        <Input 
          placeholder="Search ref key..." 
          className="max-w-sm" 
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="paytable">Paytable</SelectItem>
            <SelectItem value="reelset">Reelset</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ref Key</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Content Hash</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">View</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assets.map(asset => (
                <TableRow key={asset.id}>
                  <TableCell className="font-medium">{asset.ref_key}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="uppercase text-[10px]">
                      {asset.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {asset.content_hash?.substring(0, 8)}...
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(asset.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Sheet>
                      <SheetTrigger asChild>
                        <Button size="sm" variant="ghost">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </SheetTrigger>
                      <SheetContent className="w-[400px] sm:w-[540px]">
                        <SheetHeader>
                          <SheetTitle>Asset Content: {asset.ref_key}</SheetTitle>
                        </SheetHeader>
                        <div className="mt-4 h-[80vh] overflow-auto border rounded p-2 bg-slate-950 text-green-400 font-mono text-xs">
                          <pre>{JSON.stringify(asset.content, null, 2)}</pre>
                        </div>
                      </SheetContent>
                    </Sheet>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default MathAssetsPage;