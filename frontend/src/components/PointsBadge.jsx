import React, { useEffect, useState } from 'react';

export default function PointsBadge({ userId }) {
  const [points, setPoints] = useState(0);

  useEffect(() => {
    if (!userId) return;
    fetch(`/points/${userId}`)
      .then(res => res.json())
      .then(data => setPoints(data.points));
  }, [userId]);

  return (
    <span className="badge badge-secondary" aria-label={`points ${points}`}>{points}</span>
  );
}
