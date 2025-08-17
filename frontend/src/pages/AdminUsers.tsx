import React, { useEffect, useState } from 'react';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';
import { fetchWithAuth } from '../lib/api';

interface User {
  id: string;
  email?: string;
  username?: string;
}

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchWithAuth('/admin/users');
        const data = await res.json();
        setUsers(data.users || []);
      } catch {
        setUsers([]);
      }
    }
    load();
  }, []);

  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <h2 className="text-xl font-semibold mb-4">Users</h2>
          <ul className="space-y-2">
            {users.map((u) => (
              <li key={u.id} className="flex justify-between">
                <span>{u.email || u.username || u.id}</span>
              </li>
            ))}
          </ul>
        </div>
      </AdminScaffold>
    </>
  );
}
