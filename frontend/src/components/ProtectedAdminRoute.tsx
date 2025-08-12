import React from 'react';
import { Navigate } from 'react-router-dom';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { useSession } from '../hooks/useSession';

export default function ProtectedAdminRoute({ children }: { children: JSX.Element }) {
  const { isAdmin, loading } = useSession();
  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  return children;
}
