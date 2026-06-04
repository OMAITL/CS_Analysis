import type React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

/** Legacy route: CS analysis lives on the home dashboard. */
const CsItemPage: React.FC = () => {
  const location = useLocation();
  return <Navigate to={{ pathname: '/', search: location.search }} replace />;
};

export default CsItemPage;
