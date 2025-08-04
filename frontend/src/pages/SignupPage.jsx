import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Layout from '../components/Layout';
import { sendCode, verifyCode, registerAccount } from '../api';

export default function SignupPage() {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [codeVerified, setCodeVerified] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const ref = params.get('ref');

  const handleSend = async () => {
    try {
      await sendCode(phone);
      setCodeSent(true);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleVerify = async () => {
    try {
      await verifyCode(phone, code);
      setCodeVerified(true);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleRegister = async () => {
    try {
      const res = await registerAccount({ phone, email, password, code, ref });
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
        <h2 className="text-2xl font-bold text-center">Sign up</h2>
        {error && <p className="text-red-600">{error}</p>}
        {!codeSent && (
          <div className="space-y-2">
            <input
              className="w-full p-2 border rounded"
              placeholder="Phone number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
            <button className="px-4 py-2 bg-primary text-white rounded" onClick={handleSend}>
              Send Code
            </button>
          </div>
        )}
        {codeSent && !codeVerified && (
          <div className="space-y-2">
            <input
              className="w-full p-2 border rounded"
              placeholder="Verification code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <button className="px-4 py-2 bg-primary text-white rounded" onClick={handleVerify}>
              Verify Code
            </button>
          </div>
        )}
        {codeVerified && (
          <div className="space-y-2">
            <input
              className="w-full p-2 border rounded"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              className="w-full p-2 border rounded"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button className="px-4 py-2 bg-primary text-white rounded" onClick={handleRegister}>
              Register
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
