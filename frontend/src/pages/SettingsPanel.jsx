import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  Settings, Building2, Globe, DollarSign, CreditCard, Shield, Gamepad2,
  Mail, Scale, Wrench, Key, Palette, AlertTriangle, GitBranch, FileText,
  Plus, Edit, Trash2, Download, Upload, Play, RefreshCw, Eye
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';

const SettingsPanel = () => {
  const [activeTab, setActiveTab] = useState("brands");
  const [brands, setBrands] = useState([]);
  const [domains, setDomains] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [paymentProviders, setPaymentProviders] = useState([]);
  const [countryRules, setCountryRules] = useState([]);
  const [platformDefaults, setPlatformDefaults] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [maintenanceSchedules, setMaintenanceSchedules] = useState([]);
  const [configVersions, setConfigVersions] = useState([]);
  
  const [isBrandModalOpen, setIsBrandModalOpen] = useState(false);
  const [newBrand, setNewBrand] = useState({
    brand_name: '',
    default_currency: 'USD',
    default_language: 'en'
  });

  const fetchData = async () => {
    try {
      if (activeTab === 'brands') setBrands((await api.get('/v1/settings/brands')).data);
      if (activeTab === 'domains') setDomains((await api.get('/v1/settings/domains')).data);
      if (activeTab === 'currencies') setCurrencies((await api.get('/v1/settings/currencies')).data);
      if (activeTab === 'payment') setPaymentProviders((await api.get('/v1/settings/payment-providers')).data);
      if (activeTab === 'countries') setCountryRules((await api.get('/v1/settings/country-rules')).data);
      if (activeTab === 'defaults') setPlatformDefaults((await api.get('/v1/settings/platform-defaults')).data);
      if (activeTab === 'api-keys') setApiKeys((await api.get('/v1/settings/api-keys')).data);
      if (activeTab === 'maintenance') setMaintenanceSchedules((await api.get('/v1/settings/maintenance')).data);
      if (activeTab === 'versions') setConfigVersions((await api.get('/v1/settings/config-versions')).data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateBrand = async () => {
    try {
      await api.post('/v1/settings/brands', newBrand);
      setIsBrandModalOpen(false);
      fetchData();
      toast.success('Marka olu\u015fturuldu');
    } catch { toast.error('Ba\u015far\u0131s\u0131z'); }
  };

  const handleSyncRates = async () => {
    try {
      await api.post('/v1/settings/currencies/sync-rates');
      toast.success('D\u00f6viz kurlar\u0131 g\u00fcncellendi');
    } catch { toast.error('Ba\u015far\u0131s\u0131z'); }
  };

  const handleGenerateAPIKey = async () => {
    try {
      const result = await api.post('/v1/settings/api-keys/generate', { key_name: 'New API Key', owner: 'system' });
      toast.success(`API Key: ${result.data.api_key}`);
      fetchData();
    } catch { toast.error('Ba\u015far\u0131s\u0131z'); }
  };

  return (
    <div className=\"space-y-6\">
      <div className=\"flex items-center justify-between\">
        <h2 className=\"text-3xl font-bold tracking-tight flex items-center gap-2\">
          <Settings className=\"w-8 h-8 text-blue-600\" /> \u2699\ufe0f Settings Panel (Multi-Tenant)
        </h2>
        <Button onClick={fetchData}><RefreshCw className=\"w-4 h-4 mr-2\" /> Yenile</Button>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <ScrollArea className=\"w-full whitespace-nowrap rounded-md border\">
          <TabsList className=\"w-full flex justify-start\">
            <TabsTrigger value=\"brands\"><Building2 className=\"w-4 h-4 mr-2\" /> \ud83c\udfed Brands</TabsTrigger>
            <TabsTrigger value=\"domains\"><Globe className=\"w-4 h-4 mr-2\" /> \ud83c\udf0d Domains</TabsTrigger>
            <TabsTrigger value=\"currencies\"><DollarSign className=\"w-4 h-4 mr-2\" /> \ud83d\udcb1 Currencies</TabsTrigger>
            <TabsTrigger value=\"payment\"><CreditCard className=\"w-4 h-4 mr-2\" /> \ud83d\udcb3 Payment</TabsTrigger>
            <TabsTrigger value=\"countries\"><Shield className=\"w-4 h-4 mr-2\" /> \ud83d\udeab\ud83c\udf0d Countries</TabsTrigger>
            <TabsTrigger value=\"games\"><Gamepad2 className=\"w-4 h-4 mr-2\" /> \ud83c\udfae Games</TabsTrigger>
            <TabsTrigger value=\"communication\"><Mail className=\"w-4 h-4 mr-2\" /> \ud83d\udce1 Communication</TabsTrigger>
            <TabsTrigger value=\"regulatory\"><Scale className=\"w-4 h-4 mr-2\" /> \u2696\ufe0f Regulatory</TabsTrigger>
            <TabsTrigger value=\"defaults\"><Wrench className=\"w-4 h-4 mr-2\" /> \ud83d\udee0\ufe0f Defaults</TabsTrigger>
            <TabsTrigger value=\"api-keys\"><Key className=\"w-4 h-4 mr-2\" /> \ud83d\udd11 API Keys</TabsTrigger>
            <TabsTrigger value=\"theme\"><Palette className=\"w-4 h-4 mr-2\" /> \ud83c\udfa8 Theme</TabsTrigger>
            <TabsTrigger value=\"maintenance\"><AlertTriangle className=\"w-4 h-4 mr-2\" /> \u26d4 Maintenance</TabsTrigger>
            <TabsTrigger value=\"versions\"><GitBranch className=\"w-4 h-4 mr-2\" /> \ud83e\uddec Versions</TabsTrigger>
            <TabsTrigger value=\"audit\"><FileText className=\"w-4 h-4 mr-2\" /> \ud83e\uddfe Audit</TabsTrigger>
          </TabsList>
        </ScrollArea>

        {/* 1\ufe0f\u20e3 BRANDS */}
        <TabsContent value=\"brands\" className=\"mt-4\">
          <Card>
            <CardHeader className=\"flex flex-row items-center justify-between\">
              <div>
                <CardTitle className=\"flex items-center gap-2\">\ud83c\udfed Tenants / Brands</CardTitle>
                <CardDescription>Multi-brand y\u00f6netimi</CardDescription>
              </div>
              <Dialog open={isBrandModalOpen} onOpenChange={setIsBrandModalOpen}>
                <DialogTrigger asChild>
                  <Button><Plus className=\"w-4 h-4 mr-2\" /> Add Brand</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Yeni Marka</DialogTitle></DialogHeader>
                  <div className=\"space-y-4 py-4\">
                    <div className=\"space-y-2\">
                      <Label>Brand Name</Label>
                      <Input value={newBrand.brand_name} onChange={e=>setNewBrand({...newBrand, brand_name: e.target.value})} />
                    </div>
                    <div className=\"space-y-2\">
                      <Label>Default Currency</Label>
                      <Select value={newBrand.default_currency} onValueChange={v=>setNewBrand({...newBrand, default_currency: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value=\"USD\">USD</SelectItem>
                          <SelectItem value=\"EUR\">EUR</SelectItem>
                          <SelectItem value=\"TRY\">TRY</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button onClick={handleCreateBrand} className=\"w-full\">Olu\u015ftur</Button>
                  </div>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Brand Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Currency</TableHead>
                    <TableHead>Language</TableHead>
                    <TableHead>Countries</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {brands.map(brand => (
                    <TableRow key={brand.id}>
                      <TableCell className=\"font-medium\">{brand.brand_name}</TableCell>
                      <TableCell><Badge variant={brand.status === 'active' ? 'default' : 'secondary'}>{brand.status}</Badge></TableCell>
                      <TableCell>{brand.default_currency}</TableCell>
                      <TableCell>{brand.default_language}</TableCell>
                      <TableCell>{brand.country_availability?.length || 0}</TableCell>
                      <TableCell className=\"text-xs\">{new Date(brand.created_at).toLocaleDateString('tr-TR')}</TableCell>
                      <TableCell>
                        <div className=\"flex gap-1\">
                          <Button size=\"sm\" variant=\"ghost\"><Edit className=\"w-4 h-4\" /></Button>
                          <Button size=\"sm\" variant=\"ghost\"><Download className=\"w-4 h-4\" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {brands.length === 0 && <p className=\"text-center text-muted-foreground py-8\">Hen\u00fcz marka yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 2\ufe0f\u20e3 DOMAINS */}
        <TabsContent value=\"domains\" className=\"mt-4\">
          <Card>
            <CardHeader>
              <CardTitle className=\"flex items-center gap-2\">\ud83c\udf0d Domains & Markets</CardTitle>
            </CardHeader>
            <CardContent>
              <p className=\"text-muted-foreground\">Domain y\u00f6netimi yak\u0131nda eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 3\ufe0f\u20e3 CURRENCIES */}
        <TabsContent value=\"currencies\" className=\"mt-4\">
          <Card>
            <CardHeader className=\"flex flex-row items-center justify-between\">
              <div>
                <CardTitle className=\"flex items-center gap-2\">\ud83d\udcb1 Currencies & Exchange Rates</CardTitle>
              </div>
              <Button onClick={handleSyncRates}><RefreshCw className=\"w-4 h-4 mr-2\" /> Sync Rates</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Currency</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Exchange Rate</TableHead>
                    <TableHead>Min Deposit</TableHead>
                    <TableHead>Max Deposit</TableHead>
                    <TableHead>Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currencies.map(curr => (
                    <TableRow key={curr.id}>
                      <TableCell className=\"font-medium\">{curr.currency_code}</TableCell>
                      <TableCell>{curr.symbol}</TableCell>
                      <TableCell>{curr.exchange_rate.toFixed(4)}</TableCell>
                      <TableCell>${curr.min_deposit}</TableCell>
                      <TableCell>${curr.max_deposit}</TableCell>
                      <TableCell className=\"text-xs\">{new Date(curr.updated_at).toLocaleDateString('tr-TR')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4\ufe0f\u20e3 PAYMENT */}
        <TabsContent value=\"payment\" className=\"mt-4\">
          <Card>
            <CardHeader>
              <CardTitle className=\"flex items-center gap-2\">\ud83d\udcb3 Payment Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className=\"text-muted-foreground\">\u00d6deme sa\u011flay\u0131c\u0131 y\u00f6netimi yak\u0131nda eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 5\ufe0f\u20e3 COUNTRIES */}
        <TabsContent value=\"countries\" className=\"mt-4\">
          <Card>
            <CardHeader>
              <CardTitle className=\"flex items-center gap-2\">\ud83d\udeab\ud83c\udf0d Country Rules & Geoblocking</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Country</TableHead>
                    <TableHead>Allowed</TableHead>
                    <TableHead>Games</TableHead>
                    <TableHead>Bonuses</TableHead>
                    <TableHead>KYC Level</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {countryRules.map(rule => (
                    <TableRow key={rule.id}>
                      <TableCell className=\"font-medium\">{rule.country_name} ({rule.country_code})</TableCell>
                      <TableCell><Badge variant={rule.is_allowed ? 'default' : 'destructive'}>{rule.is_allowed ? '\u2705 Yes' : '\u274c No'}</Badge></TableCell>
                      <TableCell>{rule.games_allowed ? '\u2705' : '\u274c'}</TableCell>
                      <TableCell>{rule.bonuses_allowed ? '\u2705' : '\u274c'}</TableCell>
                      <TableCell><Badge variant=\"outline\">Level {rule.kyc_level}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 6\ufe0f\u20e3-8\ufe0f\u20e3 Placeholders */}
        <TabsContent value=\"games\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\ud83c\udfae Game Availability Rules</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value=\"communication\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\ud83d\udce1 Email / SMS / Push Providers</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value=\"regulatory\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\u2696\ufe0f Compliance & Regulatory</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        {/* 9\ufe0f\u20e3 PLATFORM DEFAULTS */}
        <TabsContent value=\"defaults\" className=\"mt-4\">
          <Card>
            <CardHeader>
              <CardTitle className=\"flex items-center gap-2\">\ud83d\udee0\ufe0f Platform Defaults</CardTitle>
            </CardHeader>
            <CardContent>
              {platformDefaults && (
                <div className=\"grid grid-cols-2 gap-4\">
                  <div className=\"space-y-2\">
                    <Label>Default Language</Label>
                    <Input value={platformDefaults.default_language} readOnly />
                  </div>
                  <div className=\"space-y-2\">
                    <Label>Default Currency</Label>
                    <Input value={platformDefaults.default_currency} readOnly />
                  </div>
                  <div className=\"space-y-2\">
                    <Label>Session Timeout (min)</Label>
                    <Input type=\"number\" value={platformDefaults.session_timeout_minutes} readOnly />
                  </div>
                  <div className=\"space-y-2\">
                    <Label>API Rate Limit (per min)</Label>
                    <Input type=\"number\" value={platformDefaults.api_rate_limit_per_minute} readOnly />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* \ud83d\udd1f API KEYS */}
        <TabsContent value=\"api-keys\" className=\"mt-4\">
          <Card>
            <CardHeader className=\"flex flex-row items-center justify-between\">
              <div>
                <CardTitle className=\"flex items-center gap-2\">\ud83d\udd11 API Keys & Webhooks</CardTitle>
              </div>
              <Button onClick={handleGenerateAPIKey}><Plus className=\"w-4 h-4 mr-2\" /> Generate Key</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Key Name</TableHead>
                    <TableHead>Key Hash</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiKeys.map(key => (
                    <TableRow key={key.id}>
                      <TableCell className=\"font-medium\">{key.key_name}</TableCell>
                      <TableCell className=\"font-mono text-xs\">{key.key_hash}</TableCell>
                      <TableCell>{key.owner}</TableCell>
                      <TableCell><Badge variant={key.status === 'active' ? 'default' : 'secondary'}>{key.status}</Badge></TableCell>
                      <TableCell className=\"text-xs\">{new Date(key.created_at).toLocaleDateString('tr-TR')}</TableCell>
                      <TableCell>
                        <Button size=\"sm\" variant=\"destructive\">Revoke</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Remaining tabs */}
        <TabsContent value=\"theme\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\ud83c\udfa8 Theme & UI Branding</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value=\"maintenance\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\u26d4 Maintenance & Downtime</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Bak\u0131m planlar\u0131 yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value=\"versions\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\ud83e\uddec Config Versions & Deployment</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Versiyon y\u00f6netimi yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value=\"audit\" className=\"mt-4\">
          <Card><CardHeader><CardTitle>\ud83e\uddfe Config Audit Log</CardTitle></CardHeader>
          <CardContent><p className=\"text-muted-foreground\">Audit log yak\u0131nda eklenecek</p></CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPanel;
