import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function SignupPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const ref = params.get('ref');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = { username, email, password };
    if (ref) payload.referral_code = ref;
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('user_id', data.user_id);
      navigate('/');
    } else {
      const err = await res.json();
      setError(err.detail || 'Registration failed');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <form onSubmit={handleSubmit} className="w-80 p-4 bg-white rounded shadow space-y-3">
        <h2 className="mb-2 text-xl font-semibold text-center">Sign up</h2>
        {error && <p className="text-red-600">{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full px-3 py-2 border rounded"
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 border rounded"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 border rounded"
        />
        <button
          type="submit"
          className="w-full py-2 text-white bg-blue-600 rounded hover:bg-blue-700"
        >
          Register
        </button>
      </form>
    </div>
  );
}

