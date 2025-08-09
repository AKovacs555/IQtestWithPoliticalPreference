export interface ShareParams {
  title?: string;
  text?: string;
  url: string;
  hashtags?: string[];
}

const DEFAULT_HASHTAGS = (import.meta.env.VITE_SOCIAL_HASHTAGS || 'IQArena,IQTest')
  .split(',')
  .map((h) => h.replace(/^#/, ''));

export async function shareResult({ title, text, url, hashtags }: ShareParams) {
  const tags = hashtags && hashtags.length ? hashtags : DEFAULT_HASHTAGS;
  const tagText = tags.map((t) => `#${t}`).join(' ');
  const plainText = text || '';
  const fullText = plainText ? `${plainText} ${tagText}` : tagText;
  if (navigator.share) {
    try {
      await navigator.share({ title, text: fullText, url });
      return true;
    } catch (err) {
      console.warn('Share cancelled or failed', err);
    }
  }
  const encodedUrl = encodeURIComponent(url);
  const encodedText = encodeURIComponent(plainText);
  const encodedTags = encodeURIComponent(tags.join(','));
  // Open X/Twitter share as primary fallback
  const twitter = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}&hashtags=${encodedTags}`;
  window.open(twitter, '_blank');
  return false;
}

export function buildFacebookShareUrl(url: string) {
  return `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
}

export function buildLineShareUrl(url: string) {
  return `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(url)}`;
}
