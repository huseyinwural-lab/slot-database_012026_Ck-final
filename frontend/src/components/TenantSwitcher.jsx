import React, { useState } from 'react';
import { useCapabilities } from '../context/CapabilitiesContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Building } from 'lucide-react';

// Mock Impersonation Switcher for Owner
// In production, this would set a "X-Impersonate-Tenant" header or similar context
const TenantSwitcher = () => {
  const { isOwner, invalidateCapabilities, refreshCapabilities } = useCapabilities();
  const [impersonating, setImpersonating] = useState(
    typeof window !== 'undefined' ? (localStorage.getItem('impersonate_tenant_id') || 'default') : 'default'
  );

  if (!isOwner) return null;

  return (
    <div className="flex items-center gap-2 mr-4 border-r border-border pr-4">
        <Building className="w-4 h-4 text-muted-foreground" />
        <Select
            value={impersonating}
            onValueChange={(val) => {
              setImpersonating(val);
              if (typeof window !== 'undefined') {
                if (val === 'default') {
                  localStorage.removeItem('impersonate_tenant_id');
                } else {
                  localStorage.setItem('impersonate_tenant_id', val);
                }
              }
              invalidateCapabilities?.();
              refreshCapabilities?.({ force: true });
            }}
        >
            <SelectTrigger className="w-[180px] h-8 text-xs border-dashed">
                <SelectValue placeholder="Context: Global" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="default">Global Context</SelectItem>
                <SelectItem value="demo">Demo Tenant</SelectItem>
                <SelectItem value="demo_renter">Demo Renter Casino</SelectItem>
                <SelectItem value="vip_casino">VIP Casino Operator</SelectItem>
            </SelectContent>
        </Select>
    </div>
  );
};

export default TenantSwitcher;
