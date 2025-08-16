import React from 'react';

export default function AdminScaffold({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="max-w-6xl mx-auto px-4 md:px-8 py-6 md:py-10 space-y-6"
      data-b-spec="admin-scaffold"
    >
      {children}
    </div>
  );
}

