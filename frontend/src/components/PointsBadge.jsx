import React, { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function PointsBadge({ userId }) {
  const [points, setPoints] = useState(0);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API_BASE}/points/${userId}`)
      .then(res => res.json())
      .then(data => setPoints(data.points));
  }, [userId]);

  return (
    <span className="badge badge-secondary" aria-label={`points ${points}`}>{points}</span>
  );
}
