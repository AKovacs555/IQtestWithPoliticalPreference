import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Autocomplete,
  Chip,
  Checkbox,
  IconButton,
  Stack,
  Select,
  MenuItem,
  InputLabel,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

import getCountryList from '../../lib/countryList.js';
import {
  SurveyPayload,
  createSurvey,
  updateSurvey,
} from '../../lib/api';
import { SUPPORTED_LANGUAGES } from '../../i18n/languages';

const SUPPORTED_LANGS = [
  'en',
  'ja',
  'ko',
  'zh',
  'es',
  'de',
  'fr',
  'pt',
  'ru',
  'ar',
  'id',
  'tr',
  'it',
  'pl',
  'nl',
  'vi',
];

interface SurveyEditorDialogProps {
  open: boolean;
  onClose: () => void;
  onSaved: (id?: string) => void;
  initialValue?: any;
}

interface ItemState {
  label: string;
  is_exclusive: boolean;
}

export default function SurveyEditorDialog({
  open,
  onClose,
  onSaved,
  initialValue,
}: SurveyEditorDialogProps) {
  const isEdit = Boolean(initialValue?.id);
  const [title, setTitle] = useState('');
  const [question, setQuestion] = useState('');
  const [language, setLanguage] = useState('en');
  const [choiceType, setChoiceType] = useState<'sa' | 'ma'>('sa');
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [items, setItems] = useState<ItemState[]>([]);
  const [isActive, setIsActive] = useState(true);
  useTranslation();
  const supported = SUPPORTED_LANGS;

  useEffect(() => {
    if (initialValue) {
      setTitle(initialValue.title || '');
      setQuestion(initialValue.question || '');
      setLanguage(initialValue.language || initialValue.lang || 'en');
      setChoiceType(initialValue.choice_type || 'sa');
      setCountryCodes(initialValue.country_codes || []);
      setItems(
        (initialValue.items || []).map((it: any) => ({
          label: it.label ?? it.body ?? '',
          is_exclusive: Boolean(it.is_exclusive),
        }))
      );
      setIsActive(initialValue.is_active ?? true);
    } else {
      setTitle('');
      setQuestion('');
      setLanguage('en');
      setChoiceType('sa');
      setCountryCodes([]);
      setItems([]);
      setIsActive(true);
    }
  }, [initialValue, open]);

  const allCountries = useMemo(() => getCountryList('en'), []);

  const addItem = () =>
    setItems((it) => [...it, { label: '', is_exclusive: false }]);

  const updateItem = (idx: number, field: keyof ItemState, value: any) => {
    setItems((it) =>
      it.map((item, i) => (i === idx ? { ...item, [field]: value } : item))
    );
  };

  const removeItem = (idx: number) =>
    setItems((it) => it.filter((_, i) => i !== idx));

  const moveItem = (from: number, to: number) => {
    setItems((it) => {
      const copy = [...it];
      const [moved] = copy.splice(from, 1);
      copy.splice(to, 0, moved);
      return copy;
    });
  };

  const handleSave = async () => {
    if (!title.trim() || !question.trim()) {
      alert('Please enter a Title and Question for the survey.');
      return;
    }
    if (items.length < 2 || items.some((i) => !i.label.trim())) {
      alert(
        'Please add at least two survey items, and ensure no item is blank.',
      );
      return;
    }
    const payload: SurveyPayload = {
      title,
      question,
      lang: language,
      language,
      choice_type: choiceType,
      country_codes: countryCodes,
      items,
      is_active: isActive,
    };
    let id: string | undefined = initialValue?.id;
    try {
      if (isEdit) {
        await updateSurvey(initialValue.id, payload);
      } else {
        const res = await createSurvey(payload);
        id = res.id;
      }
    } catch (err) {
      console.error('Survey save failed', err);
      alert('Failed to save survey: ' + err);
      return;
    }
    onSaved(id);
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{isEdit ? 'Edit Survey' : 'New Survey'}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2} mt={1}>
          <TextField
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <TextField
            label="Question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
            multiline
          />
          <FormControl>
            <FormLabel>Type</FormLabel>
            <RadioGroup
              row
              value={choiceType}
              onChange={(e) => setChoiceType(e.target.value as 'sa' | 'ma')}
            >
              <FormControlLabel value="sa" control={<Radio />} label="Single" />
              <FormControlLabel value="ma" control={<Radio />} label="Multiple" />
            </RadioGroup>
          </FormControl>
          <div>
            <Autocomplete
              multiple
              options={allCountries}
              getOptionLabel={(o) => `${o.code} ${o.name}`}
              value={allCountries.filter((c) => countryCodes.includes(c.code))}
              onChange={(_, v) => setCountryCodes(v.map((x) => x.code))}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip label={option.code} {...getTagProps({ index })} />
                ))
              }
              renderInput={(params) => (
                <TextField {...params} label="Countries" />
              )}
            />
            <Stack direction="row" spacing={1} mt={1}>
              <Button
                size="small"
                onClick={() => setCountryCodes(allCountries.map((c) => c.code))}
              >
                Select All
              </Button>
              <Button size="small" onClick={() => setCountryCodes([])}>
                Clear All
              </Button>
            </Stack>
          </div>
          <FormControl fullWidth margin="dense">
            <InputLabel>Language</InputLabel>
            <Select
              label="Language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {supported.map((lng) => (
                <MenuItem key={lng} value={lng}>
                  {SUPPORTED_LANGUAGES[lng as keyof typeof SUPPORTED_LANGUAGES] || lng}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <div>
            <Button variant="outlined" size="small" onClick={addItem}>
              Add Item
            </Button>
            <Stack spacing={1} mt={1}>
              {items.map((it, idx) => (
                <Stack
                  key={idx}
                  direction="row"
                  spacing={1}
                  alignItems="center"
                >
                  <TextField
                    label={`Item ${idx + 1}`}
                    value={it.label}
                    onChange={(e) => updateItem(idx, 'label', e.target.value)}
                    fullWidth
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={it.is_exclusive}
                        onChange={(e) =>
                          updateItem(idx, 'is_exclusive', e.target.checked)
                        }
                      />
                    }
                    label="Exclusive"
                  />
                  <IconButton
                    size="small"
                    onClick={() => moveItem(idx, idx - 1)}
                    disabled={idx === 0}
                  >
                    <ArrowUpwardIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => moveItem(idx, idx + 1)}
                    disabled={idx === items.length - 1}
                  >
                    <ArrowDownwardIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => removeItem(idx)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Stack>
              ))}
            </Stack>
          </div>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}

