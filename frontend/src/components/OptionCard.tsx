import React from 'react';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import CheckCircle from '@mui/icons-material/CheckCircle';

export function OptionCard({ label, imgSrc, selected, correct, onClick, disabled }:{
  label: string; imgSrc?: string; selected: boolean; correct?: boolean; onClick: () => void; disabled?: boolean;
}) {
  return (
    <Card elevation={selected ? 3 : 1}
      sx={{ mb: 1.25, borderWidth: 2, borderStyle: 'solid',
            borderColor: selected ? 'primary.main' : 'transparent' }}>
      <CardActionArea
        onClick={onClick}
        disabled={disabled}
        sx={{ minHeight: 'var(--tap-min)', p: 1.25, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 1 }}
        aria-pressed={selected}
      >
        {imgSrc && <img src={imgSrc} alt="" className="max-h-40 w-full object-contain mb-2" />}
        <Typography variant="body1">{label}</Typography>
        {correct && <CheckCircle aria-label="correct" className="text-green-600 ml-auto" />}
      </CardActionArea>
    </Card>
  );
}
