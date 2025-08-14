import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

import SurveyEditorDialog from '../components/admin/SurveyEditorDialog';
import { deleteSurvey, getSurveys } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function AdminSurveys() {
  const [surveys, setSurveys] = useState<any[]>([]);
  const [editing, setEditing] = useState<any | null>(null);
  const { i18n } = useTranslation();

  const load = async () => {
    try {
      const data = await getSurveys();
      setSurveys(data.surveys || []);
    } catch {
      setSurveys([]);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    if (window.confirm('Delete this survey?')) {
      await deleteSurvey(id);
      load();
    }
  };

  return (
    <Box className="space-y-4 max-w-2xl mx-auto">
      <Typography variant="h5">Surveys</Typography>
      <Button
        variant="contained"
        onClick={() => setEditing({ language: i18n.language || 'en' })}
      >
        New Survey
      </Button>
      <Stack spacing={2} mt={2}>
        {surveys.map((s) => (
          <Box
            key={s.id}
            display="flex"
            alignItems="center"
            justifyContent="space-between"
          >
            <div>
              <Typography variant="subtitle1">{s.title}</Typography>
              <Stack direction="row" spacing={1} mt={0.5}>
                <Chip label={s.lang} size="small" />
                <Chip label={s.choice_type} size="small" />
                {(s.country_codes || []).map((c: string) => (
                  <Chip key={c} label={c} size="small" />
                ))}
              </Stack>
            </div>
            <div>
              <IconButton onClick={() => setEditing(s)}>
                <EditIcon />
              </IconButton>
              <IconButton onClick={() => handleDelete(s.id)}>
                <DeleteIcon />
              </IconButton>
            </div>
          </Box>
        ))}
      </Stack>
      <SurveyEditorDialog
        open={Boolean(editing)}
        initialValue={editing || undefined}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          load();
        }}
      />
    </Box>
  );
}

