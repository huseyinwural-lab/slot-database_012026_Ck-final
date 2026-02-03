import { 
  LayoutDashboard, Users, CreditCard, ShieldAlert, 
  Gamepad2, Gift, MessageSquare, Settings, LogOut,
  ListChecks, ToggleRight, Search, FlaskConical,
  FileText, Megaphone, BarChart3, Globe, Handshake,
  AlertOctagon, UserCog, ScrollText, Scale, Crown,
  KeyRound, Building, TrendingUp, Power, DollarSign,
  Bot, FileCode
} from 'lucide-react';

export const MENU_ITEMS = [
  // CORE
  { key: 'core.dashboard', section: 'Core', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { key: 'core.players', section: 'Core', label: 'Players', icon: Users, path: '/players' },
  { key: 'core.finance', section: 'Core', label: 'Finance', icon: DollarSign, path: '/finance', ownerOnly: true },
  { key: 'core.withdrawals', section: 'Core', label: 'Withdrawals', icon: DollarSign, path: '/finance/withdrawals', ownerOnly: true },
  { key: 'core.all_revenue', section: 'Core', label: 'All Revenue', icon: TrendingUp, path: '/revenue', ownerOnly: true },
  { key: 'core.my_revenue', section: 'Core', label: 'My Revenue', icon: TrendingUp, path: '/my-revenue', ownerOnly: false, tenantOnly: true }, // Logic handled in render
  { key: 'core.games', section: 'Core', label: 'Games', icon: Gamepad2, path: '/games' },
  { key: 'core.vip_games', section: 'Core', label: 'VIP Games', icon: Crown, path: '/vip-games', className: 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/50' },

  // OPERATIONS
  { key: 'ops.kyc', section: 'Operations', label: 'KYC Verification', icon: FileText, path: '/kyc', feature: 'can_manage_kyc' },
  { key: 'ops.crm', section: 'Operations', label: 'CRM & Comms', icon: Megaphone, path: '/crm', feature: 'can_use_crm' },
  { key: 'ops.bonuses', section: 'Operations', label: 'Bonuses', icon: Gift, path: '/bonuses', feature: 'can_manage_bonus' },
  { key: 'ops.affiliates', section: 'Operations', label: 'Affiliates', icon: Handshake, path: '/affiliates', feature: 'can_manage_affiliates' },
  { key: 'ops.kill_switch', section: 'Operations', label: 'Kill Switch', icon: Power, path: '/kill-switch', ownerOnly: true, feature: 'can_use_kill_switch' },
  { key: 'ops.support', section: 'Operations', label: 'Support', icon: MessageSquare, path: '/support' },

  // RISK & COMPLIANCE
  { key: 'risk.rules', section: 'Risk & Compliance', label: 'Risk Rules', icon: AlertOctagon, path: '/risk', ownerOnly: true },
  { key: 'risk.fraud', section: 'Risk & Compliance', label: 'Fraud Check', icon: ShieldAlert, path: '/fraud', ownerOnly: true },
  { key: 'risk.approvals', section: 'Risk & Compliance', label: 'Approval Queue', icon: ListChecks, path: '/approvals', ownerOnly: true },
  { key: 'risk.rg', section: 'Risk & Compliance', label: 'Responsible Gaming', icon: Scale, path: '/rg', ownerOnly: true },

  // GAME ENGINE
  { key: 'engine.robots', section: 'Game Engine', label: 'Robots', icon: Bot, path: '/robots', feature: 'can_use_game_robot' },
  { key: 'engine.math', section: 'Game Engine', label: 'Math Assets', icon: FileCode, path: '/math-assets', feature: 'can_use_game_robot' },

  // SYSTEM
  { key: 'sys.cms', section: 'System', label: 'CMS', icon: Globe, path: '/cms', ownerOnly: true },
  { key: 'sys.reports', section: 'System', label: 'Reports', icon: BarChart3, path: '/reports', feature: 'can_view_reports' },
  { key: 'sys.logs', section: 'System', label: 'Logs', icon: ScrollText, path: '/logs', ownerOnly: true },
  { key: 'sys.audit', section: 'System', label: 'Audit Log', icon: ScrollText, path: '/audit', ownerOnly: true },
  { key: 'sys.admins', section: 'System', label: 'Admin Users', icon: UserCog, path: '/admins', feature: 'can_manage_admins' },
  { key: 'sys.tenants', section: 'System', label: 'Tenants', icon: Building, path: '/tenants', ownerOnly: true },
  { key: 'sys.keys', section: 'System', label: 'API Keys', icon: KeyRound, path: '/keys', ownerOnly: true },
  { key: 'sys.features', section: 'System', label: 'Feature Flags', icon: ToggleRight, path: '/features', ownerOnly: true, feature: 'can_manage_experiments' },
  { key: 'sys.simulator', section: 'System', label: 'Simulator', icon: FlaskConical, path: '/simulator', feature: 'can_use_game_robot' },
  { key: 'sys.settings', section: 'System', label: 'Settings', icon: Settings, path: '/settings', ownerOnly: true },

  // (Coming soon items removed for launch readiness)
];
