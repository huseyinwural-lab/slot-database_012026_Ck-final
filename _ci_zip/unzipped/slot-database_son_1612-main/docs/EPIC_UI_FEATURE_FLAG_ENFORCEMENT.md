# 🎯 EPIC: UI Feature Flag Enforcement

**EPIC ID:** UI-FE-001  
**Priority:** P0 (Critical for Production)  
**Estimated Effort:** Medium (2-3 sessions)  
**Status:** PLANNED

---

## 📝 Problem Statement

**Current State:**
- Backend tenant feature enforcement (`ensure_tenant_feature` guards) çalışıyor
- Frontend henüz tenant capabilities'den habersiz
- Kullanıcılar disabled modüllerin menülerini görebiliyor
- Direkt URL ile disabled modüle erişim mümkün → backend'de 403 alıyor ama UX kötü

**Desired State:**
- Frontend tenant capabilities'i anlıyor ve UI'ı buna göre adapte ediyor
- Disabled features'ın menü item'ları gizli
- Direkt URL erişimi route-level guard ile engelleniyor
- Kullanıcı "Module Disabled" friendly ekranı görüyor
- 403 spam yok, tek tip kullanıcı deneyimi

---

## 🎯 Acceptance Criteria

### Must-Have (P0)
1. ✅ Backend `GET /api/v1/tenant/capabilities` endpoint çalışıyor
2. ✅ Frontend login sonrası capabilities fetch ediyor ve context'te saklıyor
3. ✅ Sidebar menü item'ları feature flag'e göre conditional render
4. ✅ `RequireFeature` HOC/guard implementasyonu
5. ✅ Disabled modül için user-friendly "Module Disabled" ekranı
6. ✅ Direkt URL erişiminde guard çalışıyor ve 403 toast yerine ekran gösteriyor

### Nice-to-Have (P1)
- ⚪ Admin settings'de tenant'ın mevcut feature'larını görme UI'ı
- ⚪ Super admin için tenant feature toggle UI'ı
- ⚪ Feature usage analytics (hangi feature ne sıklıkla kullanılıyor)

---

## 📐 Technical Design

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Login Flow                                          │  │
│  │  ↓                                                   │  │
│  │  Fetch /api/v1/tenant/capabilities                  │  │
│  │  ↓                                                   │  │
│  │  Store in CapabilitiesContext                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Sidebar (Layout.jsx)                               │  │
│  │  • Check capability before rendering menu item     │  │
│  │  • Hidden if feature disabled                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Route Guards (RequireFeature HOC)                  │  │
│  │  • Wrap protected routes                            │  │
│  │  • Check capability before rendering component     │  │
│  │  • Redirect to ModuleDisabled screen if no access  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                       │
│                                                             │
│  GET /api/v1/tenant/capabilities                           │
│  • Extract tenant_id from JWT                              │
│  • Fetch tenant document from DB                           │
│  • Return feature flags as JSON                            │
│  • Cache response (optional)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Plan

### Phase 1: Backend Capabilities Endpoint (Estimated: 30 min)

#### Task 1.1: Create Capabilities Endpoint
**File:** `/app/backend/app/routes/tenant.py`

**Implementation:**
```python
from app.models.common import FeatureFlags  # Pydantic model

@router.get("/capabilities", response_model=FeatureFlags)
async def get_tenant_capabilities(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Return current user's tenant feature flags
    Used by frontend to conditionally render UI elements
    """
    tenant_id = current_user.get("tenant_id")
    
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {
            "_id": 0,
            "can_manage_admins": 1,
            "can_manage_bonus": 1,
            "can_use_game_robot": 1,
            "can_edit_configs": 1,
            "can_manage_kyc": 1,
            "can_view_reports": 1
        }
    )
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Return with defaults if fields missing
    return {
        "can_manage_admins": tenant.get("can_manage_admins", False),
        "can_manage_bonus": tenant.get("can_manage_bonus", False),
        "can_use_game_robot": tenant.get("can_use_game_robot", False),
        "can_edit_configs": tenant.get("can_edit_configs", False),
        "can_manage_kyc": tenant.get("can_manage_kyc", True),
        "can_view_reports": tenant.get("can_view_reports", True)
    }
```

#### Task 1.2: Create Pydantic Model
**File:** `/app/backend/app/models/common.py`

**Implementation:**
```python
class FeatureFlags(BaseModel):
    """Tenant feature flags for UI enforcement"""
    can_manage_admins: bool = False
    can_manage_bonus: bool = False
    can_use_game_robot: bool = False
    can_edit_configs: bool = False
    can_manage_kyc: bool = True
    can_view_reports: bool = True
```

#### Task 1.3: Test Endpoint
**Test Command:**
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@casino.com","password":"Admin123!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -X GET "$API_URL/api/v1/tenant/capabilities" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "can_manage_admins": true,
  "can_manage_bonus": true,
  "can_use_game_robot": true,
  "can_edit_configs": true,
  "can_manage_kyc": true,
  "can_view_reports": true
}
```

---

### Phase 2: Frontend Context & Hooks (Estimated: 45 min)

#### Task 2.1: Create CapabilitiesContext
**File:** `/app/frontend/src/context/CapabilitiesContext.jsx` (NEW)

**Implementation:**
```javascript
import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const { user } = useContext(AuthContext);
  const [capabilities, setCapabilities] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchCapabilities();
    } else {
      setCapabilities(null);
      setLoading(false);
    }
  }, [user]);

  const fetchCapabilities = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/v1/tenant/capabilities`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCapabilities(data);
      } else {
        console.error('Failed to fetch capabilities');
        setCapabilities({});
      }
    } catch (error) {
      console.error('Error fetching capabilities:', error);
      setCapabilities({});
    } finally {
      setLoading(false);
    }
  };

  const hasFeature = (featureKey) => {
    if (!capabilities) return false;
    return capabilities[featureKey] === true;
  };

  return (
    <CapabilitiesContext.Provider value={{ capabilities, loading, hasFeature }}>
      {children}
    </CapabilitiesContext.Provider>
  );
};

export const useCapabilities = () => {
  const context = useContext(CapabilitiesContext);
  if (!context) {
    throw new Error('useCapabilities must be used within CapabilitiesProvider');
  }
  return context;
};
```

#### Task 2.2: Wrap App with Provider
**File:** `/app/frontend/src/App.js`

**Modification:**
```javascript
import { CapabilitiesProvider } from './context/CapabilitiesContext';

function App() {
  return (
    <AuthProvider>
      <CapabilitiesProvider>
        {/* Existing routes */}
      </CapabilitiesProvider>
    </AuthProvider>
  );
}
```

---

### Phase 3: Sidebar Menu Conditional Rendering (Estimated: 30 min)

#### Task 3.1: Update Layout.jsx
**File:** `/app/frontend/src/components/Layout.jsx`

**Modification:**
```javascript
import { useCapabilities } from '../context/CapabilitiesContext';

const Layout = ({ children }) => {
  const { hasFeature } = useCapabilities();

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', feature: null },
    { path: '/players', icon: Users, label: 'Players', feature: null },
    { path: '/finance', icon: DollarSign, label: 'Finance', feature: null },
    { path: '/games', icon: Gamepad2, label: 'Games', feature: null },
    
    // Feature-gated items
    { path: '/bonuses', icon: Gift, label: 'Bonuses', feature: 'can_manage_bonus' },
    { path: '/game-configs', icon: Settings, label: 'Game Configs', feature: 'can_edit_configs' },
    { path: '/game-robot', icon: Bot, label: 'Game Robot', feature: 'can_use_game_robot' },
    { path: '/admin-management', icon: Shield, label: 'Admin Management', feature: 'can_manage_admins' },
    
    { path: '/reports', icon: BarChart3, label: 'Reports', feature: 'can_view_reports' },
    { path: '/api-keys', icon: Key, label: 'API Keys', feature: null },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white shadow-lg">
        <nav className="mt-8">
          {menuItems.map((item) => {
            // Hide if feature required but not enabled
            if (item.feature && !hasFeature(item.feature)) {
              return null;
            }

            return (
              <Link
                key={item.path}
                to={item.path}
                className={/* existing classes */}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};
```

---

### Phase 4: Route-Level Guards (Estimated: 45 min)

#### Task 4.1: Create RequireFeature Component
**File:** `/app/frontend/src/components/RequireFeature.jsx` (NEW)

**Implementation:**
```javascript
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useCapabilities } from '../context/CapabilitiesContext';
import ModuleDisabled from '../pages/ModuleDisabled';

const RequireFeature = ({ feature, children }) => {
  const { capabilities, loading, hasFeature } = useCapabilities();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!hasFeature(feature)) {
    return <ModuleDisabled featureName={feature} />;
  }

  return children;
};

export default RequireFeature;
```

#### Task 4.2: Create ModuleDisabled Page
**File:** `/app/frontend/src/pages/ModuleDisabled.jsx` (NEW)

**Implementation:**
```javascript
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldOff } from 'lucide-react';

const ModuleDisabled = ({ featureName }) => {
  const navigate = useNavigate();

  const featureLabels = {
    'can_manage_admins': 'Admin Management',
    'can_manage_bonus': 'Bonus Management',
    'can_use_game_robot': 'Game Robot',
    'can_edit_configs': 'Game Configuration',
    'can_manage_kyc': 'KYC Management',
    'can_view_reports': 'Reports'
  };

  const displayName = featureLabels[featureName] || 'This Module';

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
        <ShieldOff className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Module Disabled</h1>
        <p className="text-gray-600 mb-6">
          Your tenant does not have access to the <strong>{displayName}</strong> module.
          Please contact your administrator to enable this feature.
        </p>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};

export default ModuleDisabled;
```

#### Task 4.3: Wrap Protected Routes
**File:** `/app/frontend/src/App.js`

**Modification:**
```javascript
import RequireFeature from './components/RequireFeature';

<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/accept-invite" element={<AcceptInvite />} />
  
  <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/players" element={<Players />} />
    <Route path="/finance" element={<Finance />} />
    <Route path="/games" element={<GameManagement />} />
    
    {/* Feature-gated routes */}
    <Route
      path="/bonuses"
      element={
        <RequireFeature feature="can_manage_bonus">
          <BonusManagement />
        </RequireFeature>
      }
    />
    <Route
      path="/game-configs"
      element={
        <RequireFeature feature="can_edit_configs">
          <GameConfigPage />
        </RequireFeature>
      }
    />
    <Route
      path="/game-robot"
      element={
        <RequireFeature feature="can_use_game_robot">
          <GameRobot />
        </RequireFeature>
      }
    />
    <Route
      path="/admin-management"
      element={
        <RequireFeature feature="can_manage_admins">
          <AdminManagement />
        </RequireFeature>
      }
    />
    
    <Route path="/reports" element={<Reports />} />
    <Route path="/api-keys" element={<APIKeysPage />} />
  </Route>
</Routes>
```

---

## 🧪 Testing Plan

### Unit Tests
- [ ] `hasFeature()` hook returns correct boolean
- [ ] `RequireFeature` renders children when feature enabled
- [ ] `RequireFeature` shows ModuleDisabled when feature disabled
- [ ] Sidebar hides items correctly based on capabilities

### Integration Tests
- [ ] Login flow fetches capabilities
- [ ] Capabilities context updates on user change
- [ ] Direct URL navigation triggers guard
- [ ] Backend 403 errors no longer reach user (caught by guard)

### E2E Testing Scenarios

#### Scenario 1: Full Access User
1. Login with `admin@casino.com`
2. Verify all menu items visible
3. Navigate to each module successfully
4. No "Module Disabled" screens

#### Scenario 2: Limited Access User
1. Create tenant with `can_manage_bonus=false`
2. Create user under that tenant
3. Login
4. Verify "Bonuses" menu item hidden
5. Try direct URL: `/bonuses` → Shows "Module Disabled" screen
6. Click "Return to Dashboard" → Redirects to `/dashboard`

#### Scenario 3: No Capabilities (Edge Case)
1. Simulate API failure (capabilities fetch 500)
2. Verify app doesn't crash
3. All feature-gated items hidden (fail-safe)
4. User can still access Dashboard, Players, etc.

---

## 📊 Success Metrics

### Functional Metrics
- ✅ Zero 403 errors in browser console for feature-blocked actions
- ✅ Users cannot access disabled modules via URL
- ✅ Menu items correctly hidden for all test scenarios

### Performance Metrics
- ✅ Capabilities fetch time < 200ms
- ✅ No noticeable UI lag on login
- ✅ Context re-renders optimized (no unnecessary fetches)

### UX Metrics
- ✅ "Module Disabled" screen clear and actionable
- ✅ No confusing error messages
- ✅ Smooth transition between enabled/disabled states

---

## 🚀 Deployment Strategy

### Pre-Deployment
1. Complete backend endpoint (`/capabilities`)
2. Test with curl + manual DB manipulation
3. Complete frontend context + hooks
4. Test in dev environment with different tenant configs

### Deployment
1. Deploy backend changes first (backwards compatible)
2. Verify `/capabilities` endpoint live
3. Deploy frontend changes
4. Smoke test with real users

### Post-Deployment
1. Monitor error logs for 403s (should decrease)
2. Collect user feedback on "Module Disabled" screen
3. Verify analytics show correct feature usage patterns

---

## 📝 Open Questions / Decisions Needed

1. **Caching Strategy:**
   - Should we cache capabilities in localStorage?
   - If yes, how do we invalidate cache when tenant settings change?
   - **Recommendation:** Start without cache, add if performance issue

2. **Super Admin Override:**
   - Should super admins bypass all feature checks?
   - **Recommendation:** Add `is_super_admin` flag in backend and skip checks if true

3. **Feature Toggle UI:**
   - Should we build a UI for admins to toggle tenant features?
   - **Recommendation:** Nice-to-have for P1, not blocking P0

4. **Error Handling:**
   - What if capabilities fetch fails mid-session?
   - **Recommendation:** Keep last known capabilities, show warning banner

---

## 🔗 Related Documents

- `/app/backend/app/constants/modules.py` (Existing feature flag definitions)
- `/app/backend/app/utils/features.py` (Existing backend guards)
- `/app/docs/PROD_CHECKLIST.md` (Production readiness checklist)

---

## ✅ Definition of Done

- [ ] Backend endpoint implemented and tested
- [ ] Frontend context + hooks implemented
- [ ] Sidebar conditional rendering working
- [ ] Route guards implemented
- [ ] ModuleDisabled page created
- [ ] All protected routes wrapped with guards
- [ ] E2E testing completed (2 scenarios minimum)
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] User acceptance testing passed
- [ ] Deployed to production