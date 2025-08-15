import { Drawer, List, ListItemButton, ListItemText, IconButton, ListItem } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import type { NavItem } from './types';

export default function MobileDrawer({
  items,
  buttonClassName = '',
}: {
  items: NavItem[];
  buttonClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <IconButton
        aria-label="menu"
        onClick={() => setOpen(true)}
        size="small"
        className={buttonClassName}
      >
        <MenuIcon />
      </IconButton>
      <Drawer anchor="left" open={open} onClose={() => setOpen(false)}>
        <List sx={{ width: 300 }}>
          {items.map((it, i) =>
            it.element ? (
              <ListItem key={i}>{it.element}</ListItem>
            ) : (
              <ListItemButton
                key={i}
                component={it.href && !it.onClick ? NavLink : 'button'}
                to={it.href}
                onClick={(e) => {
                  it.onClick?.(e as any);
                  setOpen(false);
                }}
                sx={{ minHeight: 48 }}
              >
                <ListItemText primary={it.label} />
              </ListItemButton>
            ),
          )}
        </List>
      </Drawer>
    </>
  );
}
