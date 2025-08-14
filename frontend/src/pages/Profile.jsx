import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { useSession } from '../hooks/useSession';
import { getProfile, updateProfile } from '../api';

export default function Profile() {
  const { user } = useSession();
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
