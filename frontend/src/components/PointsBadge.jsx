import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/apiClient';

export default function PointsBadge({ userId, className = '' }) {
  const [points, setPoints] = useState(0);

  useEffect(() => {
    if (!userId) return;

    async function fetchPoints() {
      try {
        const data = await apiClient.get(`/points/${userId}`);
        setPoints(data?.points ?? 0);
      } catch {
        setPoints(0);
      }
    }

    fetchPoints();
  }, [userId]);

  return (
    <span
      className={`flex items-center h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)] ${className}`}
      aria-label={`points ${points}`}
    >
      {points}
    </span>
  );
}
