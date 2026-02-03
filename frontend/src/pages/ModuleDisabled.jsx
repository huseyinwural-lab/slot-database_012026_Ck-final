import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldOff, Lock } from 'lucide-react';

const ModuleDisabled = ({ featureName, reason }) => {
  const navigate = useNavigate();

  const featureLabels = {
    'can_manage_admins': 'Admin Management',
    'can_manage_bonus': 'Bonus Management',
    'can_use_game_robot': 'Game Robot',
    'can_edit_configs': 'Game Configuration',
    'can_manage_kyc': 'KYC Management',
    'can_view_reports': 'Reports',
    'can_manage_experiments': 'Feature Flags & A/B Testing',
    'can_use_kill_switch': 'Kill Switch',
    'can_manage_affiliates': 'Affiliate Program',
    'can_use_crm': 'CRM & Communications'
  };

  let title = "Module Disabled";
  let message = "You don't have access to this module.";
  let icon = <ShieldOff className="w-16 h-16 text-red-500 mx-auto mb-4" />;

  if (reason === "owner") {
    title = "Owner Access Only";
    message = "This module is restricted to platform owners only. Please contact your administrator if you need access.";
    icon = <Lock className="w-16 h-16 text-yellow-500 mx-auto mb-4" />;
  } else if (featureName) {
    const displayName = featureLabels[featureName] || 'This Module';
    message = `Your tenant does not have access to the ${displayName} module. Please contact your platform administrator to enable this feature.`;
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
        {icon}
        <h1 className="text-2xl font-bold text-gray-800 mb-2">{title}</h1>
        <p className="text-gray-600 mb-6">{message}</p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};

export default ModuleDisabled;
