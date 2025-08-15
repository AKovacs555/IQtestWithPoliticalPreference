import React from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Navbar from '../Navbar';
import LanguageSelector from '../LanguageSelector';
import PointsBadge from '../PointsBadge';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function Header() {
  const { userId } = useSession();
  const { t } = useTranslation();

  return (
    <Box
      component="header"
      data-b-spec="header-v1"
      className="sticky top-0 z-[var(--z-header)] w-full backdrop-blur-md bg-[var(--glass)] border-b border-[var(--border)]"
    >
      <Box
        className="mx-auto flex items-center gap-4 px-4"
        sx={{ maxWidth: 'var(--container-max)', height: 'var(--header-height)' }}
      >
        <Link to="/" className="text-xl font-bold gradient-text-gold whitespace-nowrap">
          IQ Arena
        </Link>
        <Navbar />
        <Box sx={{ flexGrow: 1 }} />
        <LanguageSelector />
        <PointsBadge userId={userId} />
        {userId ? (
          <Button
            component={Link}
            to="/profile"
            size="small"
            className="whitespace-nowrap"
          >
            {t('nav.profile', { defaultValue: 'Profile' })}
          </Button>
        ) : (
          <Button
            component={Link}
            to="/login"
            size="small"
            className="whitespace-nowrap"
          >
            {t('nav.login', { defaultValue: 'Log in' })}
          </Button>
        )}
      </Box>
    </Box>
  );
}

