import React, { useEffect, useState } from 'react';
import { useSession } from '../hooks/useSession';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function PointsBadge({ className = '' }) {
  const [points, setPoints] = useState(0);
  const { session } = useSession();

  useEffect(() => {
    const accessToken = session?.access_token;
    if (!accessToken) {
      setPoints(0);
      return;
    }

    async function fetchPoints() {
      try {
        const res = await fetch(`${API_BASE}/user/credits`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        const data = await res.json().catch(() => ({}));
        setPoints(data?.points ?? 0);
      } catch {
        setPoints(0);
      }
    }

    fetchPoints();
  }, [session]);

  return (
    <span
      className={`flex items-center h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)] ${className}`}
      aria-label={`points ${points}`}
    >
      {points}
    </span>
  );
}
