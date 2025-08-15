import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Brain, Trophy, Crown } from 'lucide-react';

export default function MenuBlocks({ onStart }) {
  const { t } = useTranslation();
  return (
    <div data-b-spec="menu-block-v1" className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div onClick={onStart} className="glass-card gold-ring gold-sheen p-4 md:p-6 flex flex-col items-center text-center cursor-pointer">
        <Brain className="h-10 w-10 text-amber-300 mb-2" />
        <h3 className="text-lg font-semibold text-white">
          {t('menu.take_test', { defaultValue: 'テストを受ける' })}
        </h3>
        <p className="text-sm text-[var(--text-muted)]">
          {t('menu.take_test_desc', { defaultValue: '新しいIQテストを始めましょう' })}
        </p>
      </div>
      <Link to="/leaderboard" className="glass-card gold-ring gold-sheen p-4 md:p-6 flex flex-col items-center text-center cursor-pointer">
        <Trophy className="h-10 w-10 text-amber-300 mb-2" />
        <h3 className="text-lg font-semibold text-white">
          {t('menu.view_ranking', { defaultValue: 'ランキングを見る' })}
        </h3>
        <p className="text-sm text-[var(--text-muted)]">
          {t('menu.view_ranking_desc', { defaultValue: 'トップ成績者を確認しよう' })}
        </p>
      </Link>
      <Link to="/upgrade" className="glass-card gold-ring gold-sheen p-4 md:p-6 flex flex-col items-center text-center cursor-pointer">
        <Crown className="h-10 w-10 text-amber-300 mb-2" />
        <h3 className="text-lg font-semibold text-white">
          {t('menu.view_pricing', { defaultValue: '料金を見る' })}
        </h3>
        <p className="text-sm text-[var(--text-muted)]">
          {t('menu.view_pricing_desc', { defaultValue: 'Proプランの特典を見てみよう' })}
        </p>
      </Link>
    </div>
  );
}
