import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const RequireAuth = ({ children }) => {
  let isAuthenticated = false;
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('admin_token');
    isAuthenticated = !!token;
  }

  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default RequireAuth;
