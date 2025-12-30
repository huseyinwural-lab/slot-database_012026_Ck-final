import React, { useCallback, useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { ImageIcon, Upload, Trash2 } from 'lucide-react';
import api from '../../services/api';

const filterAssets = (assets, type) => assets.filter((a) => a.asset_type === type && !a.is_deleted);

const GameAssetsTab = ({ game }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  const [uploadDialog, setUploadDialog] = useState({ open: false, context: null });
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTags, setUploadTags] = useState('');
  const [uploadLanguage, setUploadLanguage] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);

  const [deleteDialog, setDeleteDialog] = useState({ open: false, asset: null });
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadAssets = async () => {
    if (!game) return;
    setLoading(true);
    try {
      const res = await api.get(`/v1/games/${game.id}/config/assets`);
      setAssets(res.data?.assets || []);
    } catch (err) {
      console.error(err);
      toast.error('Assets yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets();
  }, [game?.id]);

  const openUploadFor = (assetType, language = null) => {
    setUploadDialog({ open: true, context: { assetType, language } });
    setUploadFile(null);
    setUploadTags('');
    setUploadLanguage(language || '');
  };

  const handleUpload = async () => {
    if (!game || !uploadDialog.context || !uploadFile) {
      toast.error('Lütfen bir dosya seçin');
      return;
    }
    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('asset_type', uploadDialog.context.assetType);
      if (uploadLanguage) formData.append('language', uploadLanguage);
      if (uploadTags) formData.append('tags', uploadTags);

      await api.post(`/v1/games/${game.id}/config/assets/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Asset yüklendi');
      setUploadDialog({ open: false, context: null });
      await loadAssets();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || 'Asset yüklenemedi';
      toast.error(msg);
    } finally {
      setUploadLoading(false);
    }
  };

  const confirmDelete = (asset) => {
    setDeleteDialog({ open: true, asset });
  };

  const handleDelete = async () => {
    if (!game || !deleteDialog.asset) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/v1/games/${game.id}/config/assets/${deleteDialog.asset.id}`);
      toast.success('Asset kaldırıldı');
      setDeleteDialog({ open: false, asset: null });
      await loadAssets();
    } catch (err) {
      console.error(err);
      toast.error('Asset silinemedi');
    } finally {
      setDeleteLoading(false);
    }
  };

  const logos = filterAssets(assets, 'logo');
  const thumbnails = filterAssets(assets, 'thumbnail');
  const banners = filterAssets(assets, 'banner');

  const findLogoByLang = (lang) => logos.find((a) => a.language === lang) || null;

  const renderLogoSlot = (label, langCode) => {
    const asset = findLogoByLang(langCode);
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">Logo ({label})</CardTitle>
            <CardDescription>Bu dil için lobi/logoda kullanılacak logo.</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => openUploadFor('logo', langCode)}>
            <Upload className="w-4 h-4 mr-1" /> Upload
          </Button>
        </CardHeader>
        <CardContent>
          {asset ? (
            <div className="flex items-center gap-4">
              <div className="w-24 h-24 bg-slate-900 border border-slate-800 rounded flex items-center justify-center overflow-hidden">
                <img src={asset.url} alt={asset.filename} className="object-contain max-w-full max-h-full" />
              </div>
              <div className="space-y-1 text-xs">
                <div className="font-mono break-all">{asset.filename}</div>
                <div className="text-muted-foreground">{(asset.size_bytes / 1024).toFixed(1)} KB</div>
                <div className="text-muted-foreground">{asset.mime_type}</div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-500 hover:text-red-600 px-0"
                  onClick={() => confirmDelete(asset)}
                >
                  <Trash2 className="w-4 h-4 mr-1" /> Delete
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <ImageIcon className="w-4 h-4" />
              Bu dil için logo yüklü değil.
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* LOGO SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {renderLogoSlot('TR', 'tr')}
        {renderLogoSlot('EN', 'en')}
      </div>

      {/* THUMBNAILS SECTION */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">Thumbnails</CardTitle>
            <CardDescription>Lobi listeleri ve oyun kutuları için küçük görseller.</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => openUploadFor('thumbnail')}>
            <Upload className="w-4 h-4 mr-1" /> Add Thumbnail
          </Button>
        </CardHeader>
        <CardContent>
          {thumbnails.length === 0 ? (
            <div className="text-xs text-muted-foreground">Henüz thumbnail yüklenmemiş.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Preview</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Tags</TableHead>
                  <TableHead>Language</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {thumbnails.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <div className="w-16 h-10 bg-slate-900 border border-slate-800 rounded overflow-hidden flex items-center justify-center">
                        <img src={a.url} alt={a.filename} className="object-cover w-full h-full" />
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs break-all">{a.filename}</TableCell>
                    <TableCell className="text-xs">
                      {(a.tags || []).length > 0 ? (
                        a.tags.map((t) => (
                          <Badge key={t} variant="outline" className="mr-1 mb-0.5">
                            {t}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs">{a.language || '-'}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500 hover:text-red-600"
                        onClick={() => confirmDelete(a)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* BANNERS SECTION */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">Promo Banners</CardTitle>
            <CardDescription>Kampanya, promo ve vitrin banner görselleri.</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => openUploadFor('banner')}>
            <Upload className="w-4 h-4 mr-1" /> Add Banner
          </Button>
        </CardHeader>
        <CardContent>
          {banners.length === 0 ? (
            <div className="text-xs text-muted-foreground">Henüz promo banner yüklenmemiş.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Preview</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Tags</TableHead>
                  <TableHead>Language</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {banners.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <div className="w-28 h-12 bg-slate-900 border border-slate-800 rounded overflow-hidden flex items-center justify-center">
                        <img src={a.url} alt={a.filename} className="object-cover w-full h-full" />
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs break-all">{a.filename}</TableCell>
                    <TableCell className="text-xs">
                      {(a.tags || []).length > 0 ? (
                        a.tags.map((t) => (
                          <Badge key={t} variant="outline" className="mr-1 mb-0.5">
                            {t}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs">{a.language || '-'}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500 hover:text-red-600"
                        onClick={() => confirmDelete(a)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* UPLOAD DIALOG */}
      <Dialog open={uploadDialog.open} onOpenChange={(open) => setUploadDialog({ open, context: uploadDialog.context })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              Upload {uploadDialog.context?.assetType} {uploadDialog.context?.language ? `(${uploadDialog.context.language.toUpperCase()})` : ''}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="space-y-2">
              <label className="text-xs font-medium">File</label>
              <Input
                type="file"
                accept="image/png,image/jpeg"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
              <p className="text-[10px] text-muted-foreground">Sadece PNG/JPEG desteklenir.</p>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium">Tags (optional)</label>
              <Input
                value={uploadTags}
                onChange={(e) => setUploadTags(e.target.value)}
                placeholder="lobby,16x9,promo"
              />
            </div>
            {!uploadDialog.context?.language && (
              <div className="space-y-2">
                <label className="text-xs font-medium">Language (optional)</label>
                <Input
                  value={uploadLanguage}
                  onChange={(e) => setUploadLanguage(e.target.value)}
                  placeholder="tr, en ..."
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadDialog({ open: false, context: null })}>
              İptal
            </Button>
            <Button onClick={handleUpload} disabled={uploadLoading || !uploadFile}>
              {uploadLoading ? 'Uploading...' : 'Upload'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* DELETE CONFIRM DIALOG */}
      <Dialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, asset: deleteDialog.asset })}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Asset&apos;i kaldır</DialogTitle>
          </DialogHeader>
          <p className="text-xs text-muted-foreground mt-2">
            Bu asset&apos;i kaldırmak istediğine emin misin? Oyun loglarında asset_deleted olarak işaretlenecektir.
          </p>
          {deleteDialog.asset && (
            <div className="mt-3 p-2 border border-slate-800 rounded bg-slate-950 text-xs font-mono break-all">
              {deleteDialog.asset.filename} ({deleteDialog.asset.asset_type})
            </div>
          )}
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setDeleteDialog({ open: false, asset: null })}>
              Vazgeç
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleteLoading}>
              {deleteLoading ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GameAssetsTab;
