import React from 'react';
import { Brain } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function TakeTestCard({ onStart }) {
  const { t } = useTranslation();
  return (
    <div
      data-b-spec="card-start"
      onClick={onStart}
      className="gold-card p-5 min-h-20 text-center cursor-pointer flex flex-col items-center justify-center"
    >
      <Brain className="h-10 w-10 text-amber-300 mb-2" />
      <h3 className="text-lg font-semibold text-white">
        {t('menu.take_test', { defaultValue: 'テストを受ける' })}
      </h3>
      <p className="text-sm text-[var(--text-muted)]">
        {t('menu.take_test_desc', { defaultValue: '新しいIQテストを始めましょう' })}
      </p>
    </div>
  );
}
