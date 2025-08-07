import React from 'react';
import Layout from '../components/Layout.jsx';
import { Outlet } from 'react-router-dom';

export default function AdminLayout() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}
