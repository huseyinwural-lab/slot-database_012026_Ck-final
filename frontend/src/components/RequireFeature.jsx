import React from 'react';
import { useCapabilities } from '../context/CapabilitiesContext';
import ModuleDisabled from '../pages/ModuleDisabled';

const RequireFeature = ({ feature, requireOwner = false, children }) => {
  const { capabilities, loading, hasFeature, isOwner } = useCapabilities();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Check owner requirement
  if (requireOwner && !isOwner) {
    return <ModuleDisabled reason="owner" />;
  }

  // Check feature requirement
  if (feature && !hasFeature(feature)) {
    return <ModuleDisabled featureName={feature} />;
  }

  return children;
};

export default RequireFeature;
