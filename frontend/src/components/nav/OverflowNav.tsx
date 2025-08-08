import { useEffect, useRef, useState } from 'react';
import { Box, Button, IconButton, Menu, MenuItem } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';

// Generic overflow group: render inline until space runs out, spill rest into "More"
export default function OverflowNav({
  items,
  gap = 0.5,
}: { items: Array<any>; gap?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [visibleCount, setVisibleCount] = useState(items.length);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const ro = new ResizeObserver(() => {
      const el = containerRef.current;
      if (!el) return;
      const max = el.clientWidth - 56; // reserve ~"More" button width
      let used = 0,
        count = 0;
      for (let i = 0; i < items.length; i++) {
        const w = itemRefs.current[i]?.offsetWidth ?? 0;
        if (w === 0) {
          count = i;
          break;
        }
        if (used + w > max) break;
        used += w;
        count = i + 1;
      }
      setVisibleCount(Math.max(0, count));
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [items.length]);

  const visible = items.slice(0, visibleCount);
  const overflow = items.slice(visibleCount);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap, minHeight: '48px' }}>
      <Box
        ref={containerRef}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap,
          flexWrap: 'nowrap',
          overflow: 'hidden',
        }}
      >
        {visible.map((it, i) => (
          <Button
            key={i}
            ref={(n) => (itemRefs.current[i] = n)}
            onClick={it.onClick}
            href={it.href}
            size="small"
            sx={{ minHeight: '48px' }}
          >
            {it.element ?? it.label}
          </Button>
        ))}
      </Box>

      {overflow.length > 0 && (
        <>
          <IconButton
            aria-label="more"
            onClick={(e) => setAnchorEl(e.currentTarget)}
            size="small"
          >
            <MoreVertIcon />
          </IconButton>
          <Menu
            open={Boolean(anchorEl)}
            anchorEl={anchorEl}
            onClose={() => setAnchorEl(null)}
          >
            {overflow.map((it, i) => (
              <MenuItem
                key={i}
                onClick={(e) => {
                  setAnchorEl(null);
                  it.onClick?.(e as any);
                }}
                component={it.href ? 'a' : 'li'}
                href={it.href}
              >
                {it.label}
              </MenuItem>
            ))}
          </Menu>
        </>
      )}
    </Box>
  );
}
