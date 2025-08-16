import React, { useEffect, useState } from 'react';
import { Box, Chip, IconButton, Stack, Typography } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

import SurveyEditorDialog from '../components/admin/SurveyEditorDialog';
import { deleteSurvey, getSurveys, updateSurveyStatus } from '../lib/api';
import { useTranslation } from 'react-i18next';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

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
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <Box className="space-y-4 max-w-2xl mx-auto">
            <Typography variant="h5">Surveys</Typography>
            <button
              className="btn-solid"
              onClick={() => setEditing({ lang: i18n.language || 'en' })}
              data-b-spec="admin-button-size"
            >
              New Survey
            </button>
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
                <Chip label={s.type} size="small" />
                {(s.target_countries || []).map((c: string) => (
                  <Chip key={c} label={c} size="small" />
                ))}
                {(s.target_genders || []).map((g: string) => (
                  <Chip key={g} label={g} size="small" />
                ))}
              </Stack>
            </div>
            <div>
              <Chip
                label={s.status === 'approved' ? 'Approved' : 'Draft'}
                onClick={async () => {
                  const newStatus = s.status === 'approved' ? 'draft' : 'approved';
                  await updateSurveyStatus(s.id, { status: newStatus, is_active: s.is_active });
                  load();
                }}
                color={s.status === 'approved' ? 'success' : 'default'}
                sx={{ mr: 1, cursor: 'pointer' }}
              />
              <IconButton onClick={() => setEditing(s)} sx={{ width: 44, height: 44 }}>
                <EditIcon />
              </IconButton>
              <IconButton onClick={() => handleDelete(s.id)} sx={{ width: 44, height: 44 }}>
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
        </div>
      </AdminScaffold>
    </>
  );
}

