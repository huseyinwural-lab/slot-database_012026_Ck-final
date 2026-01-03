import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Palette, Save } from 'lucide-react';
import { toast } from 'sonner';

const ThemeSettings = ({ brands }) => {
  const safeBrands = Array.isArray(brands) ? brands : [];
  const [selectedBrand, setSelectedBrand] = useState('');
  const effectiveSelectedBrand = selectedBrand || safeBrands[0]?.id || '';
  const [theme, setTheme] = useState({
    brand_id: '',
    logo_url: '',
    color_palette: { primary: '#000000', secondary: '#ffffff' }
  });

  useEffect(() => {
    const fetchTheme = async (brandId) => {
      try {
        const res = await api.get(`/v1/settings/theme/${brandId}`);
        setTheme(res.data);
      } catch {
        // Reset if not found
        setTheme({ brand_id: brandId, logo_url: '', color_palette: { primary: '#000000', secondary: '#ffffff' } });
      }
    };

    if (effectiveSelectedBrand) fetchTheme(effectiveSelectedBrand);
  }, [effectiveSelectedBrand]);

  const handleSave = async () => {
    try {
      await api.post('/v1/settings/theme', { ...theme, brand_id: effectiveSelectedBrand });
      toast.success('Tema kaydedildi');
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">Theme & UI Branding</CardTitle>
        <CardDescription>Marka bazlı arayüz özelleştirme</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label>Select Brand</Label>
          <Select value={effectiveSelectedBrand} onValueChange={setSelectedBrand}>
            <SelectTrigger><SelectValue placeholder="Marka Seç" /></SelectTrigger>
            <SelectContent>
              {safeBrands.map(b => <SelectItem key={b.id} value={b.id}>{b.brand_name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        {effectiveSelectedBrand && (
          <div className="space-y-4 border p-4 rounded-lg">
            <div className="space-y-2">
              <Label>Logo URL</Label>
              <Input value={theme.logo_url} onChange={e => setTheme({...theme, logo_url: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Primary Color</Label>
                <div className="flex gap-2">
                  <Input type="color" className="w-12 p-1 h-10" value={theme.color_palette.primary} onChange={e => setTheme({...theme, color_palette: {...theme.color_palette, primary: e.target.value}})} />
                  <Input value={theme.color_palette.primary} onChange={e => setTheme({...theme, color_palette: {...theme.color_palette, primary: e.target.value}})} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Secondary Color</Label>
                <div className="flex gap-2">
                  <Input type="color" className="w-12 p-1 h-10" value={theme.color_palette.secondary} onChange={e => setTheme({...theme, color_palette: {...theme.color_palette, secondary: e.target.value}})} />
                  <Input value={theme.color_palette.secondary} onChange={e => setTheme({...theme, color_palette: {...theme.color_palette, secondary: e.target.value}})} />
                </div>
              </div>
            </div>
            <Button onClick={handleSave} className="w-full"><Save className="w-4 h-4 mr-2" /> Kaydet</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ThemeSettings;
