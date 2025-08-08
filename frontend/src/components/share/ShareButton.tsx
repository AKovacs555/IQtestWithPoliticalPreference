import React from 'react';
import Button from '@mui/material/Button';
import ShareIcon from '@mui/icons-material/Share';
import { shareResult, ShareParams } from '../../utils/share';

interface Props extends ShareParams {
  label?: string;
}

export default function ShareButton({ title, text, url, hashtags, label }: Props) {
  const handleClick = () => {
    void shareResult({ title, text, url, hashtags });
  };
  return (
    <Button onClick={handleClick} startIcon={<ShareIcon />}>{label || 'Share'}</Button>
  );
}
