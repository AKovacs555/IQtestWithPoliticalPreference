import { Drawer, List, ListItemButton, ListItemText, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useState } from 'react';

export default function MobileDrawer({ items }: { items: Array<any> }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <IconButton aria-label="menu" onClick={() => setOpen(true)} size="small">
        <MenuIcon />
      </IconButton>
      <Drawer anchor="left" open={open} onClose={() => setOpen(false)}>
        <List sx={{ width: 300 }}>
          {items.map((it, i) => (
            <ListItemButton
              key={i}
              component={it.href ? 'a' : 'button'}
              href={it.href}
              onClick={it.onClick}
              sx={{ minHeight: 48 }}
            >
              <ListItemText primary={it.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
    </>
  );
}
