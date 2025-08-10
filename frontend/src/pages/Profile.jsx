import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { useAuth } from '../auth/useAuth';
import { getProfile, updateProfile } from '../api';

export default function Profile() {
  const { user, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    if (!user) return;
    getProfile().then((d) => setUsername(d.username || '')); 
  }, [user]);

  const save = async (e) => {
    e.preventDefault();
    try {
      await updateProfile({ username });
      setStatus('Saved');
    } catch (err) {
      setStatus(err.message || 'Error');
    }
  };

  if (loading) return <AppShell><div className="p-4">Loading...</div></AppShell>;
  if (!user) return <AppShell><div className="p-4">Please log in.</div></AppShell>;

  return (
    <AppShell>
      <form onSubmit={save} className="max-w-md mx-auto p-4 space-y-2">
        <label className="block">Username</label>
        <input
          className="input input-bordered w-full"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button type="submit" className="btn btn-primary mt-2">Save</button>
        {status && <p className="text-sm">{status}</p>}
      </form>
    </AppShell>
  );
}
