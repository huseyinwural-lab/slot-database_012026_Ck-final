# 🏗️ Güvenlik ve Mimari İyileştirme Planı

## 📊 Mevcut Durum vs Hedef

### ✅ Tamamlananlar
- [x] Backend tenant scoping (admin, players, games, transactions)
- [x] Tenant feature flags (can_use_game_robot, can_edit_configs, etc.)
- [x] Admin Invite Flow
- [x] Tenant-Admin ilişkisi
- [x] Basic CORS, Rate Limiting, Health Probes

### ❌ Eksikler (Kullanıcı Listesinden)

**P0 - Kritik:**
- [ ] Owner vs Tenant role ayrımı **NET DEĞİL**
- [ ] Revenue dashboard - Owner tüm tenant'ları göremez
- [ ] Tüm endpoint'lerde tenant scoping audit
- [ ] Frontend RequireFeature() route guard
- [ ] Sidebar conditional rendering (feature flags)

**P1 - Önemli:**
- [ ] Tenant rol kırılımı (Tenant Admin / Operations / Finance)
- [ ] Owner Finance Dashboard (tüm tenant'lar + filter)
- [ ] Tenant Finance Dashboard (sadece kendi)
- [ ] Owner paneli ve Tenant paneli **AYRI BUILD**

**P2 - İleri Seviye:**
- [ ] Oyun kodu güvenliği (WASM, signed URLs, watermark)
- [ ] Asset encryption
- [ ] IL2CPP + obfuscation

---

## 🎯 Implementation Plan

### **PHASE 1: Backend Role & Revenue (P0)** ⚡ 3-4 saat

#### Task 1.1: Owner vs Tenant Role Enforcement
**Hedef:** `is_super_admin` veya `tenant_type` ile net ayrım

**Backend Changes:**
```python
# app/models/domain/admin.py
class AdminUser(BaseModel):
    ...
    role: str  # "Super Admin", "Tenant Admin", "Operations", "Finance"
    is_platform_owner: bool = False  # YENİ: Owner mu tenant mi?
    tenant_id: str
```

**Kontrol Mantığı:**
```python
def is_owner(admin: AdminUser) -> bool:
    return admin.is_platform_owner or admin.role == "Super Admin"

# Her endpoint'te:
if not is_owner(current_admin):
    query["tenant_id"] = current_admin.tenant_id
```

---

#### Task 1.2: Revenue Dashboard Endpoints

**Owner Endpoint:**
```python
@router.get("/reports/revenue/all-tenants")
async def get_all_tenants_revenue(
    from_date: datetime,
    to_date: datetime,
    tenant_id: Optional[str] = None,  # Filter by specific tenant
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Only owner can access
    if not is_owner(current_admin):
        raise HTTPException(403, "Owner access only")
    
    query = {
        "created_at": {"$gte": from_date, "$lte": to_date}
    }
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    # Aggregate by tenant
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$tenant_id",
            "total_bets": {"$sum": "$bet_amount"},
            "total_wins": {"$sum": "$win_amount"},
            "ggr": {"$sum": {"$subtract": ["$bet_amount", "$win_amount"]}},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(None)
    return results
```

**Tenant Endpoint:**
```python
@router.get("/reports/revenue/my-tenant")
async def get_my_tenant_revenue(
    from_date: datetime,
    to_date: datetime,
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Tenant can only see their own
    tenant_id = current_admin.tenant_id
    
    query = {
        "tenant_id": tenant_id,
        "created_at": {"$gte": from_date, "$lte": to_date}
    }
    
    # Aggregate metrics
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_bets": {"$sum": "$bet_amount"},
            "total_wins": {"$sum": "$win_amount"},
            "ggr": {"$sum": {"$subtract": ["$bet_amount", "$win_amount"]}},
        }}
    ]
    
    result = await db.transactions.aggregate(pipeline).to_list(1)
    return result[0] if result else {}
```

---

#### Task 1.3: Endpoint Audit Checklist

**Kritik Endpoint'ler - Tenant Scoping Kontrolü:**

| Endpoint | Mevcut Durum | Aksiyon |
|----------|--------------|---------|
| `/players` | ✅ Filtreleniyor | - |
| `/games` | ✅ Filtreleniyor | - |
| `/finance/transactions` | ✅ Filtrelendi | - |
| `/admin/users` | ✅ Filtrelendi | - |
| `/admin/sessions` | ✅ Filtrelendi | - |
| `/bonuses` | ✅ Filtreleniyor | - |
| `/tenants` | ❌ Herkes görüyor | **Owner-only yap** |
| `/dashboard/stats` | ⚠️ Kontrol et | Tenant scoping ekle |
| `/reports/*` | ❌ Yok | Yeni endpoint'ler ekle |

**Düzeltme:**
```python
@router.get("/tenants")
async def list_tenants(current_admin: AdminUser = Depends(get_current_admin)):
    # Only owner can see all tenants
    if not is_owner(current_admin):
        raise HTTPException(403, "Owner access only")
    
    # Owner görür
    tenants = await db.tenants.find().to_list(100)
    return tenants
```

---

### **PHASE 2: Frontend Role-Based UI (P0)** ⚡ 2-3 saat

#### Task 2.1: RequireFeature HOC
```jsx
// src/components/RequireFeature.jsx
const RequireFeature = ({ feature, children, requireOwner = false }) => {
  const { capabilities, loading, isOwner } = useCapabilities();

  if (loading) return <LoadingSpinner />;

  // Owner check
  if (requireOwner && !isOwner) {
    return <ModuleDisabled reason="Owner access only" />;
  }

  // Feature check
  if (feature && !capabilities[feature]) {
    return <ModuleDisabled featureName={feature} />;
  }

  return children;
};
```

#### Task 2.2: Sidebar Conditional Rendering
```jsx
const menuItems = [
  // Owner-only
  { 
    path: '/tenants', 
    label: 'Tenants', 
    icon: Building,
    requireOwner: true  // SADECE OWNER
  },
  { 
    path: '/revenue-dashboard', 
    label: 'All Revenue', 
    icon: TrendingUp,
    requireOwner: true
  },
  
  // Tenant with feature flags
  { 
    path: '/players', 
    label: 'Players', 
    icon: Users,
    feature: null  // Everyone
  },
  { 
    path: '/bonuses', 
    label: 'Bonuses', 
    icon: Gift,
    feature: 'can_manage_bonus'
  },
  { 
    path: '/game-configs', 
    label: 'Configs', 
    icon: Settings,
    feature: 'can_edit_configs',
    requireOwner: true  // Sadece owner config değiştirebilir
  },
];

// Render
{menuItems.map((item) => {
  if (item.requireOwner && !isOwner) return null;
  if (item.feature && !hasFeature(item.feature)) return null;
  
  return <MenuItem key={item.path} {...item} />;
})}
```

#### Task 2.3: CapabilitiesContext Enhancement
```jsx
export const CapabilitiesProvider = ({ children }) => {
  const { user } = useContext(AuthContext);
  const [capabilities, setCapabilities] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchCapabilities();
    }
  }, [user]);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/v1/tenant/capabilities');
      const data = response.data;
      
      setCapabilities(data.features || {});
      setIsOwner(data.is_owner || false);  // Backend'den gelecek
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
      setCapabilities({});
      setIsOwner(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <CapabilitiesContext.Provider value={{ 
      capabilities, 
      loading, 
      isOwner,  // YENİ
      hasFeature: (key) => capabilities[key] === true 
    }}>
      {children}
    </CapabilitiesContext.Provider>
  );
};
```

---

### **PHASE 3: Tenant Rol Kırılımı (P1)** ⚡ 2 saat

#### Task 3.1: Tenant-Specific Roles

**Model Update:**
```python
class TenantRole(str, Enum):
    TENANT_ADMIN = "tenant_admin"      # Full access (tenant içinde)
    OPERATIONS = "operations"          # Players, Games, Bonuses
    FINANCE = "finance"                # Reports, Revenue

class AdminUser(BaseModel):
    ...
    tenant_role: Optional[TenantRole] = TenantRole.TENANT_ADMIN
```

#### Task 3.2: Permission Matrix

| Role | Players | Games | Bonuses | Configs | Reports | Revenue | Admin Mgmt |
|------|---------|-------|---------|---------|---------|---------|------------|
| **Owner** | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **Tenant Admin** | ✅ Own | ✅ Own | ✅ Own | ❌ | ✅ Own | ✅ Own | ✅ Own |
| **Operations** | ✅ Own | ✅ View | ✅ Own | ❌ | ✅ Basic | ❌ | ❌ |
| **Finance** | ❌ | ❌ | ❌ | ❌ | ✅ Full | ✅ Full | ❌ |

---

### **PHASE 4: Owner & Tenant Ayrı Build (P1)** ⚡ 4-5 saat

#### Task 4.1: Monorepo Structure
```
/app/frontend/
  ├── src/
  │   ├── owner/           # Owner-specific components
  │   │   ├── pages/
  │   │   │   ├── AllRevenueDashboard.jsx
  │   │   │   ├── TenantsManagement.jsx
  │   │   │   └── GlobalSettings.jsx
  │   │   └── OwnerApp.jsx
  │   │
  │   ├── tenant/          # Tenant-specific components
  │   │   ├── pages/
  │   │   │   ├── MyRevenue.jsx
  │   │   │   ├── MyPlayers.jsx
  │   │   │   └── MyGames.jsx
  │   │   └── TenantApp.jsx
  │   │
  │   └── shared/          # Shared components
  │       ├── components/
  │       ├── services/
  │       └── utils/
  │
  ├── owner.html           # Owner entry point
  ├── tenant.html          # Tenant entry point
  └── vite.config.js       # Multi-entry build config
```

#### Task 4.2: Vite Multi-Entry Config
```js
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        owner: resolve(__dirname, 'owner.html'),
        tenant: resolve(__dirname, 'tenant.html')
      }
    }
  }
});
```

#### Task 4.3: Deployment Strategy
```
owner.yourdomain.com → /dist/owner/
  - Sadece owner modülleri
  - Source map kapalı
  - CSP headers

tenant.yourdomain.com → /dist/tenant/
  - Sadece tenant modülleri
  - Source map kapalı
  - Daha kısıtlı bundle
```

---

### **PHASE 5: Oyun Güvenliği (P2)** ⚡ 1 hafta+

#### Task 5.1: Server-Authoritative Game Results
```python
@router.post("/games/{game_id}/spin")
async def spin_game(
    game_id: str,
    bet_amount: float,
    player: Player = Depends(get_current_player)
):
    # RNG ve payout hesaplaması SERVER'da
    result = calculate_game_result(game_id, bet_amount)
    
    # Result DB'ye kaydet
    await db.game_sessions.insert_one({
        "player_id": player.id,
        "game_id": game_id,
        "bet": bet_amount,
        "win": result.win_amount,
        "symbols": result.symbols,  # Encrypted
        "timestamp": datetime.now(timezone.utc)
    })
    
    # Client sadece animasyon için gerekli bilgiyi alır
    return {
        "win": result.win_amount,
        "symbols_encrypted": encrypt(result.symbols)
    }
```

#### Task 5.2: Signed URL for Game Assets
```python
def generate_game_url(game_id: str, player_id: str) -> str:
    # 5 dakika geçerli token
    token = create_signed_token({
        "game_id": game_id,
        "player_id": player_id,
        "exp": datetime.now() + timedelta(minutes=5)
    })
    
    return f"https://cdn.yourdomain.com/games/{game_id}/index.html?token={token}"
```

---

## 📋 Öncelik Matrisi

| Task | Öncelik | Etki | Süre | Bağımlılık |
|------|---------|------|------|------------|
| **Owner vs Tenant Role** | P0 | 🔴 Kritik | 2h | - |
| **Revenue Endpoints** | P0 | 🔴 Kritik | 2h | Role |
| **Endpoint Audit** | P0 | 🔴 Kritik | 1h | - |
| **RequireFeature HOC** | P0 | 🟡 Önemli | 1h | - |
| **Sidebar Conditional** | P0 | 🟡 Önemli | 1h | HOC |
| **Tenant Rol Kırılımı** | P1 | 🟡 Önemli | 2h | Role |
| **Ayrı Build** | P1 | 🟢 Nice-to-have | 4h | - |
| **Oyun Güvenliği** | P2 | 🟢 İleri seviye | 1 hafta+ | - |

---

## 🎯 Önerilen Execution Order

### **Sprint 1 (Bugün + Yarın)** - P0 Completion
1. ✅ Owner vs Tenant role enforcement (2h)
2. ✅ Revenue endpoints (owner + tenant) (2h)
3. ✅ Endpoint audit + fix (1h)
4. ✅ RequireFeature HOC (1h)
5. ✅ Sidebar conditional rendering (1h)

**Toplam: ~7 saat** → Production-ready security

---

### **Sprint 2 (Sonraki Hafta)** - P1 Features
1. Tenant rol kırılımı (2h)
2. Owner Finance Dashboard UI (3h)
3. Ayrı build stratejisi (4h)

**Toplam: ~9 saat** → Enterprise-grade

---

### **Sprint 3 (Gelecek)** - P2 Hardening
1. Server-authoritative game logic
2. Signed URL + CDN
3. WASM oyun motoru
4. Asset encryption

**Toplam: Proje bazlı**

---

## 💬 Sonraki Adım: Karar Zamanı

**Soru: Hangi sprint'i şimdi başlatmak istersiniz?**

**Seçenek A:** Sprint 1 (P0) → 7 saat → Güvenli, production-ready sistem  
**Seçenek B:** Sadece Revenue Dashboard (P0'dan bir parça) → 2 saat  
**Seçenek C:** UI Feature Flag Enforcement (önceki plan) → 2 saat

Ben **Seçenek A** öneriyorum çünkü:
- Owner vs Tenant ayrımı NET olur
- Revenue dashboard çalışır
- Tüm endpoint'ler güvenli olur
- UI feature flags da dahil

**Kararınız nedir?** 🚀
