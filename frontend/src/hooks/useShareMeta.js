import { useEffect } from 'react';

export default function useShareMeta(url) {
  useEffect(() => {
    if (!url) return;
    const og = document.querySelector('meta[property="og:image"]') || document.createElement('meta');
    og.setAttribute('property', 'og:image');
    og.content = url;
    document.head.appendChild(og);
    const tw = document.querySelector('meta[name="twitter:image"]') || document.createElement('meta');
    tw.setAttribute('name', 'twitter:image');
    tw.content = url;
    document.head.appendChild(tw);
    return () => {
      og.remove();
      tw.remove();
    };
  }, [url]);
}
