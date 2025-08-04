import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { loginAccount } from '../api';

export default function LoginPage() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await loginAccount(identifier, password);
      localStorage.setItem('authToken', res.token);
      localStorage.setItem('user_id', res.user_id);
      navigate(localStorage.getItem('survey_completed') === 'true' ? '/test' : '/survey');
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto space-y-4">
        <h2 className="text-2xl font-bold text-center">Log in</h2>
        {error && <p className="text-red-600">{error}</p>}
        <input
          className="w-full p-2 border rounded"
          placeholder="Phone or email"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
        />
        <input
          className="w-full p-2 border rounded"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="px-4 py-2 bg-primary text-white rounded" onClick={handleLogin}>
          Log in
        </button>
      </div>
    </Layout>
  );
}
