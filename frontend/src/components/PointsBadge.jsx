import React, { useEffect, useState } from 'react';
import { useSession } from '../hooks/useSession';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function PointsBadge({ userId, className = '' }) {
  const [points, setPoints] = useState(0);
  const { session } = useSession();

  useEffect(() => {
    if (!userId) return;

    async function fetchPoints() {
      const accessToken = session?.access_token;
      try {
        const res = await fetch(`${API_BASE}/points/${userId}`, {
          headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
        });
        if (res.status === 404) {
          setPoints(0);
          return;
        }
        const data = await res.json();
        setPoints(data?.points ?? 0);
      } catch {
        setPoints(0);
      }
    }

    fetchPoints();
  }, [userId, session]);

  return (
    <span
      className={`flex items-center h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)] ${className}`}
      aria-label={`points ${points}`}
    >
      {points}
    </span>
  );
}
