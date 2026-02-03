import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { 
  Settings, Building2, Globe, DollarSign, CreditCard, Shield, Gamepad2,
  Mail, Scale, Wrench, Key, Palette, AlertTriangle, GitBranch, FileText,
  RefreshCw
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

// Sub-components
import BrandSettings from '../components/settings/BrandSettings';
import CurrencySettings from '../components/settings/CurrencySettings';
import CountrySettings from '../components/settings/CountrySettings';
import ApiKeySettings from '../components/settings/ApiKeySettings';
import PaymentsPolicySettings from '../components/settings/PaymentsPolicySettings';

const COMING_SOON_TABS = new Set([
  'currencies',
  'domains',
  'payment',
  'games',
  'communication',
  'regulatory',
  'theme',
  'maintenance',
  'audit',
]);

const ComingSoonCard = ({ title, description, testId }) => (
  <Card data-testid={testId}>
    <CardHeader>
      <CardTitle>{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-muted-foreground" data-testid={`${testId}-message`}>
        {description}
      </p>
    </CardContent>
  </Card>
);

const SettingsPanel = () => {
  const [activeTab, setActiveTab] = useState("brands");
  const [brands, setBrands] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [countryRules, setCountryRules] = useState([]);
  const [platformDefaults, setPlatformDefaults] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);


  const fetchData = async (tab = activeTab) => {
    if (COMING_SOON_TABS.has(tab)) return;
    try {
      if (tab === 'brands') {
        const data = (await api.get('/v1/settings/brands')).data;
        setBrands(Array.isArray(data) ? data : []);
      }
      if (tab === 'countries') setCountryRules((await api.get('/v1/settings/country-rules')).data);
      if (tab === 'defaults') setPlatformDefaults((await api.get('/v1/settings/platform-defaults')).data);
      if (tab === 'api-keys') setApiKeys((await api.get('/v1/settings/api-keys')).data);
    } catch (err) {
      console.error(err);
    }
  };

  // Initial load
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = (await api.get('/v1/settings/brands')).data;
        if (!mounted) return;
        setBrands(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    fetchData(tab);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Settings className="w-8 h-8 text-blue-600" /> Settings Panel (Multi-Tenant)
        </h2>
        <Button onClick={fetchData} data-testid="settings-refresh-button">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>
      
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <ScrollArea className="w-full whitespace-nowrap rounded-md border">
          <TabsList className="w-full flex justify-start">
            <TabsTrigger value="brands" data-testid="settings-tab-brands"><Building2 className="w-4 h-4 mr-2" /> Brands</TabsTrigger>
            <TabsTrigger value="domains" data-testid="settings-tab-domains">
              <Globe className="w-4 h-4 mr-2" /> Domains
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-domains-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="currencies" data-testid="settings-tab-currencies">
              <DollarSign className="w-4 h-4 mr-2" /> Currencies
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-currencies-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="payment" data-testid="settings-tab-payment">
              <CreditCard className="w-4 h-4 mr-2" /> Payment Providers
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-payment-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="payments-policy" data-testid="settings-tab-payments-policy"><Scale className="w-4 h-4 mr-2" /> Payments Policy</TabsTrigger>
            <TabsTrigger value="countries" data-testid="settings-tab-countries"><Shield className="w-4 h-4 mr-2" /> Countries</TabsTrigger>
            <TabsTrigger value="games" data-testid="settings-tab-games">
              <Gamepad2 className="w-4 h-4 mr-2" /> Games
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-games-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="communication" data-testid="settings-tab-communication">
              <Mail className="w-4 h-4 mr-2" /> Communication
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-communication-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="regulatory" data-testid="settings-tab-regulatory">
              <Scale className="w-4 h-4 mr-2" /> Regulatory
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-regulatory-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="defaults" data-testid="settings-tab-defaults"><Wrench className="w-4 h-4 mr-2" /> Defaults</TabsTrigger>
            <TabsTrigger value="api-keys" data-testid="settings-tab-api-keys"><Key className="w-4 h-4 mr-2" /> API Keys</TabsTrigger>
            <TabsTrigger value="theme" data-testid="settings-tab-theme">
              <Palette className="w-4 h-4 mr-2" /> Theme
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-theme-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="maintenance" data-testid="settings-tab-maintenance">
              <AlertTriangle className="w-4 h-4 mr-2" /> Maintenance
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-maintenance-badge">Yakında</Badge>
            </TabsTrigger>
            <TabsTrigger value="versions" data-testid="settings-tab-versions"><GitBranch className="w-4 h-4 mr-2" /> Versions</TabsTrigger>
            <TabsTrigger value="audit" data-testid="settings-tab-audit">
              <FileText className="w-4 h-4 mr-2" /> Audit
              <Badge variant="secondary" className="ml-2" data-testid="settings-tab-audit-badge">Yakında</Badge>
            </TabsTrigger>
          </TabsList>
        </ScrollArea>

        {/* BRANDS */}
        <TabsContent value="brands" className="mt-4">
          <BrandSettings brands={brands} onRefresh={fetchData} />
        </TabsContent>

        {/* CURRENCIES */}
        <TabsContent value="currencies" className="mt-4">
          <ComingSoonCard
            title="Currencies"
            description="Bu özellik yakında aktif edilecektir."
            testId="settings-currencies-coming-soon"
          />
        </TabsContent>

        {/* COUNTRIES */}
        <TabsContent value="countries" className="mt-4">
          <CountrySettings countryRules={countryRules} />
        </TabsContent>

        {/* PLATFORM DEFAULTS */}
        <TabsContent value="defaults" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">Platform Defaults</CardTitle>
            </CardHeader>
            <CardContent>
              {platformDefaults && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Default Language</Label>
                    <Input value={platformDefaults.default_language} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>Default Currency</Label>
                    <Input value={platformDefaults.default_currency} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>Session Timeout (min)</Label>
                    <Input type="number" value={platformDefaults.session_timeout_minutes} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>API Rate Limit (per min)</Label>
                    <Input type="number" value={platformDefaults.api_rate_limit_per_minute} readOnly />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* API KEYS */}
        <TabsContent value="api-keys" className="mt-4">
          <ApiKeySettings apiKeys={apiKeys} onRefresh={fetchData} />
        </TabsContent>

        {/* PLACEHOLDER TABS */}
        <TabsContent value="domains" className="mt-4">
          <Card><CardHeader><CardTitle>Domains & Markets</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Domain yönetimi yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="payment" className="mt-4">
          <Card><CardHeader><CardTitle>Payment Settings</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Ödeme sağlayıcı yönetimi yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="payments-policy" className="mt-4">
          <PaymentsPolicySettings />
        </TabsContent>

        <TabsContent value="games" className="mt-4">
          <Card><CardHeader><CardTitle>Game Availability Rules</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="communication" className="mt-4">
          <Card><CardHeader><CardTitle>Email / SMS / Push Providers</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="regulatory" className="mt-4">
          <Card><CardHeader><CardTitle>Compliance & Regulatory</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="theme" className="mt-4">
          <Card><CardHeader><CardTitle>Theme & UI Branding</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="maintenance" className="mt-4">
          <Card><CardHeader><CardTitle>Maintenance & Downtime</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Bakım planları yakında eklenecek</p></CardContent></Card>
        </TabsContent>

        <TabsContent value="versions" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>About / Version</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm">
                <span className="font-medium">UI Version:</span>{' '}
                <span className="font-mono">{process.env.REACT_APP_VERSION || 'unknown'}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium">UI Git SHA:</span>{' '}
                <span className="font-mono">{process.env.REACT_APP_GIT_SHA || 'unknown'}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium">UI Build Time:</span>{' '}
                <span className="font-mono">{process.env.REACT_APP_BUILD_TIME || 'unknown'}</span>
              </div>

              <div className="pt-2">
                <Button
                  variant="outline"
                  onClick={async () => {
                    try {
                      const res = await api.get('/version');
                      toast.success(`Backend: ${res.data.version} (${res.data.git_sha})`);
                    } catch (e) {
                      toast.error('Failed to fetch backend version');
                    }
                  }}
                >
                  Check Backend Version
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <Card><CardHeader><CardTitle>Config Audit Log</CardTitle></CardHeader>
          <CardContent><p className="text-muted-foreground">Audit log yakında eklenecek</p></CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPanel;
