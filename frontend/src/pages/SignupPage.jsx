import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SignupPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
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
      <form onSubmit={handleSubmit} className="w-80 p-4 bg-white rounded shadow">
        <h2 className="mb-4 text-xl font-semibold">Create Account</h2>
        {error && <p className="text-red-600 mb-2">{error}</p>}
        <input
          type="text"
          placeholder="Username (optional)"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full px-3 py-2 mb-3 border rounded"
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 mb-3 border rounded"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 mb-4 border rounded"
          required
        />
        <button
          type="submit"
          className="w-full py-2 text-white bg-green-600 rounded hover:bg-green-700"
        >
          Sign Up
        </button>
      </form>
    </div>
  );
}

