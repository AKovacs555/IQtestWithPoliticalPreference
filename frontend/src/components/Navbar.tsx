import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ThemeToggle from './ThemeToggle';
import PointsBadge from './PointsBadge';
import LanguageSelector from './LanguageSelector';
import { useTranslation } from 'react-i18next';
import { signOut } from '../lib/auth';
import GoogleOAuthButton from './GoogleOAuthButton';
import OverflowNav from './nav/OverflowNav';
import MobileDrawer from './nav/MobileDrawer';
import type { NavItem } from './nav/types';
import { useSession } from '../hooks/useSession';

if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
  console.error('Supabase envs missing. Check Vercel project env and redeploy.');
}

export default function Navbar() {
  const { user, userId, isAdmin, loading } = useSession();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const googleEnabled = import.meta.env.VITE_DISABLE_GOOGLE !== 'true';

  const logout = () => {
    signOut().catch(() => {});
    try {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user_id');
    } catch {
      /* ignore */
    }
    navigate('/login');
  };

  const handleStart = () => {
    if (!user) navigate('/login');
    else if (!localStorage.getItem('nationality')) navigate('/select-nationality');
    else if (localStorage.getItem('demographic_completed') !== 'true') navigate('/demographics');
    else if (localStorage.getItem('survey_completed') !== 'true') navigate('/survey');
    else navigate('/quiz');
  };

  const links: NavItem[] = [
    { label: t('nav.leaderboard'), href: '/leaderboard' },
    { label: t('nav.pricing'), href: '/pricing' },
    { label: t('nav.nationality'), href: '/select-nationality' },
    { label: t('dashboard.title'), href: '/dashboard' },
    { label: t('nav.contact', { defaultValue: 'Contact' }), href: '/contact' },
  ];
  if (user) {
    links.unshift({ label: t('nav.profile', { defaultValue: 'Profile' }), href: '/profile' });
    links.unshift({ label: t('nav.daily_survey', { defaultValue: 'Daily Survey' }), href: '/daily-survey' });
  }

  // 読み込み中はメニューを確定しない（ちらつき防止）
  const adminItems: NavItem[] =
    !loading && isAdmin
      ? [{ label: t('nav.admin', { defaultValue: 'Admin' }), href: '/admin' }]
      : [];

  const items: NavItem[] = [
    ...links,
    { label: t('nav.take_quiz'), onClick: handleStart },
    ...adminItems,
  ];

  const drawerItems: NavItem[] = [...items];
  if (!user) {
    drawerItems.push(
      { label: t('nav.login', { defaultValue: 'Log in' }), href: '/login' },
      { label: t('nav.signup', { defaultValue: 'Sign up' }), href: '/signup' },
      ...(googleEnabled
        ? [
            {
              label: 'google',
              element: <GoogleOAuthButton size="small" fullWidth />,
            },
          ]
        : []),
    );
  } else {
    drawerItems.push({ label: t('nav.logout', { defaultValue: 'Log out' }), onClick: logout });
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflowX: 'auto' }}>
      <Typography
        component={Link}
        to="/"
        variant="h6"
        color="text.primary"
        sx={{ textDecoration: 'none', mr: 1 }}
      >
        IQ Test
      </Typography>
      <Box sx={{ display: { xs: 'none', md: 'block' } }}>
        <OverflowNav items={items} />
      </Box>
      <Box sx={{ flexGrow: 1 }} />
      {isMobile && <MobileDrawer items={drawerItems} />}
      <ThemeToggle />
      <LanguageSelector />
      <PointsBadge userId={userId} />
      {!user ? (
        <>
          {googleEnabled && <GoogleOAuthButton size="small" sx={{ minHeight: '48px' }} />}
          <Button component={NavLink} to="/login" size="small" sx={{ minHeight: '48px' }}>
            {t('nav.login', { defaultValue: 'Log in' })}
          </Button>
          <Button component={NavLink} to="/signup" size="small" sx={{ minHeight: '48px' }}>
            {t('nav.signup', { defaultValue: 'Sign up' })}
          </Button>
        </>
      ) : (
        <Button onClick={logout} size="small" sx={{ minHeight: '48px' }}>
          {t('nav.logout', { defaultValue: 'Log out' })}
        </Button>
      )}
    </Box>
  );
}
