export const INTERNAL_ROLES = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  ADMIN: 'ADMIN',
  OPS: 'OPS',
  SUPPORT: 'SUPPORT',
  UNKNOWN: 'UNKNOWN',
};

export const PERMISSIONS = {
  SUPPORT_VIEW: 'SUPPORT_VIEW',
  OPS_ACTIONS: 'OPS_ACTIONS',
  CREDIT_ADJUSTMENT: 'CREDIT_ADJUSTMENT',
};

const SET_SUPPORT_VIEW = new Set([
  INTERNAL_ROLES.SUPPORT,
  INTERNAL_ROLES.OPS,
  INTERNAL_ROLES.ADMIN,
  INTERNAL_ROLES.SUPER_ADMIN,
]);

const SET_OPS_ACTIONS = new Set([
  INTERNAL_ROLES.OPS,
  INTERNAL_ROLES.ADMIN,
  INTERNAL_ROLES.SUPER_ADMIN,
]);

const SET_CREDIT_ADJUSTMENT = new Set([
  INTERNAL_ROLES.ADMIN,
  INTERNAL_ROLES.SUPER_ADMIN,
]);

const PERMISSION_MATRIX = {
  [PERMISSIONS.SUPPORT_VIEW]: SET_SUPPORT_VIEW,
  [PERMISSIONS.OPS_ACTIONS]: SET_OPS_ACTIONS,
  [PERMISSIONS.CREDIT_ADJUSTMENT]: SET_CREDIT_ADJUSTMENT,
};

export function normalizeRole(rawRole) {
  const r = (rawRole || '').trim();
  if (!r) return INTERNAL_ROLES.UNKNOWN;

  const key = r.replace(/[-_]/g, ' ').trim().toUpperCase();

  if (key === 'SUPER ADMIN' || key === 'SUPERADMIN') return INTERNAL_ROLES.SUPER_ADMIN;

  // Admin aliases (treat Tenant Admin as ADMIN)
  if (
    key === 'TENANT ADMIN' ||
    key === 'TENANTADMIN' ||
    key === 'TENANT ADMINISTRATOR' ||
    key === 'ADMIN' ||
    key === 'ADMINISTRATOR'
  ) {
    return INTERNAL_ROLES.ADMIN;
  }

  // Ops aliases
  if (key === 'OPS' || key === 'OPERATIONS' || key === 'OPERATION' || key === 'OP') return INTERNAL_ROLES.OPS;

  // Support aliases
  if (key === 'SUPPORT' || key === 'CS' || key === 'CUSTOMER SUPPORT' || key === 'CUSTOMERSUPPORT') {
    return INTERNAL_ROLES.SUPPORT;
  }

  return INTERNAL_ROLES.UNKNOWN;
}

export function getEffectiveRole(admin) {
  if (admin?.is_platform_owner) return INTERNAL_ROLES.SUPER_ADMIN;
  return normalizeRole(admin?.role);
}

export function hasPermission(adminOrRole, permission) {
  const role =
    typeof adminOrRole === 'string'
      ? normalizeRole(adminOrRole)
      : getEffectiveRole(adminOrRole);

  const set = PERMISSION_MATRIX[permission];
  return !!set && set.has(role);
}

export function getAdminFromStorage() {
  try {
    const raw = localStorage.getItem('admin_user');
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
