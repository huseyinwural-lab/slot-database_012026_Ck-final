import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Switch } from '@/components/ui/switch';
import { Copy, Bot, Eye } from 'lucide-react';
import api from '../services/api';

const RobotsPage = () => {
  const [robots, setRobots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedRobot, setSelectedRobot] = useState(null);

  const fetchRobots = async () => {
    try {
      setLoading(true);
      const res = await api.get('/v1/robots', { params: { search } });
      setRobots(res.data.items || []);
    } catch (e) {
      setRobots([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRobots();
  }, [search]);

  const handleToggle = async (id) => {
    try {
      await api.post(
        `/v1/robots/${id}/toggle`,
        { reason: 'Admin UI toggle robot active state' }
      );
      fetchRobots();
      toast.success('Updated status');
    } catch {
      toast.error('Failed to toggle');
    }
  };

  const handleClone = async (id) => {
    try {
      await api.post(
        `/v1/robots/${id}/clone`,
        { reason: 'Admin UI clone robot' }
      );
      fetchRobots();
      toast.success('Cloned successfully');
    } catch {
      toast.error('Clone failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Bot className="w-8 h-8" /> Robot Registry
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <Input
          placeholder="Search robots..."
          className="max-w-sm"
          value={search}
          onChange={e => setSearch(e.target.value)}
          data-testid="robots-search-input"
        />
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Config Hash</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {robots.map(robot => (
                <TableRow key={robot.id}>
                  <TableCell className="font-medium">{robot.name}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {robot.config_hash?.substring(0, 8)}...
                  </TableCell>
                  <TableCell>
                    <Badge variant={robot.is_active ? 'default' : 'secondary'}>
                      {robot.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(robot.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right flex justify-end gap-2">
                    <Switch 
                      checked={robot.is_active} 
                      onCheckedChange={() => handleToggle(robot.id)}
                    />
                    <Button size="sm" variant="outline" onClick={() => handleClone(robot.id)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Sheet>
                      <SheetTrigger asChild>
                        <Button size="sm" variant="ghost" onClick={() => setSelectedRobot(robot)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </SheetTrigger>
                      <SheetContent className="w-[400px] sm:w-[540px]">
                        <SheetHeader>
                          <SheetTitle>Robot Config: {robot.name}</SheetTitle>
                        </SheetHeader>
                        <div className="mt-4 h-[80vh] overflow-auto border rounded p-2 bg-slate-950 text-green-400 font-mono text-xs">
                          <pre>{JSON.stringify(robot.config, null, 2)}</pre>
                        </div>
                      </SheetContent>
                    </Sheet>
                  </TableCell>
                </TableRow>
              ))}
              {robots.length === 0 && !loading && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <div className="py-10 text-center" data-testid="robots-empty-state">
                      <div className="text-sm font-medium">Henüz kayıtlı robot bulunamadı</div>
                      <div className="text-xs text-muted-foreground">Robot kayıtları oluşturulduğunda burada görünecektir.</div>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default RobotsPage;