import React, { useEffect, useState } from 'react';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function AdminPricing() {
  const [rules, setRules] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/admin/pricing_rules`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setRules(data.rules || []));
  }, []);

  const updateRule = (id, field, value) => {
    setRules(rules.map(r => (r.id === id ? { ...r, [field]: value } : r)));
  };

  const save = (rule) => {
    fetch(`${API_BASE}/admin/pricing_rules/${rule.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(rule)
    });
  };

  const filtered = rules.filter(r => r.country.toLowerCase().includes(filter.toLowerCase()));

  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <div className="space-y-4">
            <h2 className="text-2xl font-bold">Pricing Rules</h2>
            <input
              className="input input-bordered w-full md:w-64"
              placeholder="Search country"
              value={filter}
              onChange={e => setFilter(e.target.value)}
            />
            <div className="table-wrap" data-b-spec="admin-table-scroll">
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Product</th>
                    <th>Price (JPY)</th>
                    <th>Active</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(rule => (
                    <tr key={rule.id}>
                      <td>{rule.country}</td>
                      <td>{rule.product}</td>
                      <td>
                        <input
                          type="number"
                          className="input input-bordered w-24"
                          value={rule.price_jpy}
                          onChange={e => updateRule(rule.id, 'price_jpy', parseInt(e.target.value, 10) || 0)}
                        />
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          checked={rule.active}
                          onChange={e => updateRule(rule.id, 'active', e.target.checked)}
                        />
                      </td>
                      <td>
                        <button className="btn btn-sm min-h-[44px] px-4" onClick={() => save(rule)}>Save</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </AdminScaffold>
    </>
  );
}
