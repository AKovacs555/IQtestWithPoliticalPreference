import React from 'react';

interface Props {
  chunk: string;
}

export default function ErrorChunkReload({ chunk }: Props) {
  return (
    <div className="p-4 text-center">
      <p>Failed to load {chunk} chunk. Please reload.</p>
      <button
        onClick={() => window.location.reload()}
        className="btn btn-primary mt-2"
      >
        Reload
      </button>
    </div>
  );
}
