import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '../../services/api';

const getVariant = (game, key) => {
  if (!game || !game.client_variants) return null;
  return game.client_variants[key] || null;
};

const VariantCard = ({ label, typeKey, variant, onUploadClick }) => {
  const enabled = !!variant?.enabled;
  const launchUrl = variant?.launch_url || '-';

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div>
          <CardTitle className="text-sm flex items-center gap-2">
            {label}
            <Badge variant={enabled ? 'default' : 'outline'} className="text-[10px]">
              {enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </CardTitle>
          <CardDescription className="text-xs mt-1 break-all">
            Launch URL: {launchUrl}
          </CardDescription>
        </div>
        <Button size="sm" variant="outline" onClick={() => onUploadClick(typeKey)}>
          {enabled ? 'Update' : 'Upload'}
        </Button>
      </CardHeader>
      <CardContent className="text-[11px] text-muted-foreground space-y-1">
        <div>Runtime: {variant?.runtime || typeKey}</div>
        {variant?.extra?.min_version && <div>Min Version: {variant.extra.min_version}</div>}
      </CardContent>
    </Card>
  );
};

const GameClientTab = ({ game, onUpdated }) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [clientType, setClientType] = useState(null); // 'html5' | 'unity'
  const [file, setFile] = useState(null);
  const [launchUrl, setLaunchUrl] = useState('');
  const [minVersion, setMinVersion] = useState('');
  const [loading, setLoading] = useState(false);

  if (!game) return null;

  const html5Variant = getVariant(game, 'html5');
  const unityVariant = getVariant(game, 'unity');

  const openForType = (typeKey) => {
    setClientType(typeKey);
    setFile(null);
    setLaunchUrl('');
    setMinVersion('');
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!file || !clientType) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('client_type', clientType);
      if (launchUrl) formData.append('launch_url', launchUrl);
      if (minVersion) formData.append('min_version', minVersion);

      await api.post(`/v1/games/${game.id}/client-upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      toast.success(
        `Oyun istemcisi yüklendi (model: ${clientType === 'html5' ? 'HTML5' : 'Unity WebGL'}).`,
      );
      setDialogOpen(false);
      onUpdated?.();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || 'Client upload başarısız oldu.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 pt-2">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <VariantCard
          label="HTML5 Variant"
          typeKey="html5"
          variant={html5Variant}
          onUploadClick={openForType}
        />
        <VariantCard
          label="Unity WebGL Variant"
          typeKey="unity"
          variant={unityVariant}
          onUploadClick={openForType}
        />
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              Client Upload – {clientType === 'unity' ? 'Unity WebGL' : 'HTML5'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="space-y-2">
              <Label>Client Model</Label>
              <div className="flex gap-4 text-xs">
                <button
                  type="button"
                  className={`px-2 py-1 rounded border ${
                    clientType === 'html5'
                      ? 'border-blue-500 text-blue-500'
                      : 'border-slate-700 text-slate-300'
                  }`}
                  onClick={() => setClientType('html5')}
                >
                  HTML5
                </button>
                <button
                  type="button"
                  className={`px-2 py-1 rounded border ${
                    clientType === 'unity'
                      ? 'border-blue-500 text-blue-500'
                      : 'border-slate-700 text-slate-300'
                  }`}
                  onClick={() => setClientType('unity')}
                >
                  Unity WebGL
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Bundle File</Label>
              <Input
                type="file"
                accept=".zip,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <p className="text-[10px] text-muted-foreground">
                Supported: .zip WebGL build veya .json/html5 bundle metadata.
              </p>
            </div>

            <div className="space-y-2">
              <Label>Launch URL (optional)</Label>
              <Input
                value={launchUrl}
                onChange={(e) => setLaunchUrl(e.target.value)}
                placeholder="https://cdn.example.com/games/slot123/index.html"
              />
            </div>

            <div className="space-y-2">
              <Label>Min Client Version (optional)</Label>
              <Input
                value={minVersion}
                onChange={(e) => setMinVersion(e.target.value)}
                placeholder="1.0.0"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              İptal
            </Button>
            <Button onClick={handleSave} disabled={loading || !file || !clientType}>
              {loading ? 'Uploading...' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GameClientTab;
