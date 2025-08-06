import React, { useState } from 'react';
import Layout from '../components/Layout';

const CONTACT_EMAIL = import.meta.env.VITE_CONTACT_EMAIL || 'support@example.com';

export default function Contact() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const body = `${message}\n\nFrom: ${name} <${email}>`;
    const mailto = `mailto:${CONTACT_EMAIL}?subject=Contact&body=${encodeURIComponent(body)}`;
    window.location.href = mailto;
    setSent(true);
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <h1 className="text-2xl font-bold mb-4">Contact Us</h1>
        {sent ? (
          <p className="text-green-700">Thank you for reaching out!</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              required
            />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              required
            />
            <textarea
              placeholder="Message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full px-3 py-2 border rounded h-32"
              required
            />
            <button
              type="submit"
              className="w-full py-2 bg-primary text-white rounded hover:bg-primary/90"
            >
              Send
            </button>
          </form>
        )}
      </div>
    </Layout>
  );
}

