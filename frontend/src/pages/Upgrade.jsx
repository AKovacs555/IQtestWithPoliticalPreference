import React from 'react';
import AppShell from '../components/AppShell';
import { Link } from 'react-router-dom';

export default function Upgrade() {
  const handleUpgrade = (plan) => {
    // TODO: implement upgrade flow
    console.log('upgrade', plan);
  };

  return (
    <AppShell>
      <div
        data-b-spec="upgrade-v1"
        className="min-h-screen bg-amber-50 text-amber-900 py-10"
      >
        <div className="max-w-5xl mx-auto px-4 space-y-12">
          <Link
            to="/dashboard"
            className="inline-block text-sm text-amber-700 hover:text-amber-900"
          >
            ← ダッシュボードに戻る
          </Link>

          <header className="text-center space-y-2">
            <h1 className="text-4xl font-bold">アップグレード</h1>
            <p className="text-amber-700">
              Proで無制限の受験と広告最小化を楽しもう
            </p>
          </header>

          <section className="grid md:grid-cols-3 gap-8">
            {/* Free Plan */}
            <div className="relative bg-white/80 border border-amber-200 rounded-lg p-6 shadow-sm opacity-60">
              <h3 className="text-xl font-semibold mb-2">Free</h3>
              <div className="mb-4">
                <span className="text-3xl font-bold">¥0</span>
              </div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>1日1回の受験</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✖</span>
                  <span>広告最小化</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✖</span>
                  <span>限定アンケート</span>
                </li>
              </ul>
              <button
                disabled
                className="w-full py-2 rounded-md bg-gray-300 text-gray-500 cursor-not-allowed"
              >
                現在のプラン
              </button>
            </div>

            {/* Monthly Plan */}
            <div className="relative bg-white border-2 border-amber-400 rounded-lg p-6 shadow-md">
              <div className="absolute -top-3 left-0 right-0 flex justify-center">
                <span className="bg-amber-400 text-white text-xs font-semibold px-3 py-1 rounded-b">
                  POPULAR
                </span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Pro 月額</h3>
              <div className="mb-4">
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">¥1,200</span>
                  <span className="text-sm line-through text-amber-600">¥1,500</span>
                  <span className="text-xs bg-amber-100 text-amber-600 px-2 py-1 rounded">
                    20% OFF
                  </span>
                </div>
              </div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>受験無制限</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>広告最小化</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>限定アンケート</span>
                </li>
              </ul>
              <button
                className="w-full py-2 rounded-md bg-amber-500 hover:bg-amber-600 text-white font-semibold"
                onClick={() => handleUpgrade('pro-monthly')}
              >
                今すぐ加入
              </button>
            </div>

            {/* Yearly Plan */}
            <div className="relative bg-white/80 border border-amber-200 rounded-lg p-6 shadow-sm">
              <h3 className="text-xl font-semibold mb-2">Pro 年額</h3>
              <div className="mb-4">
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">¥10,000</span>
                  <span className="text-sm line-through text-amber-600">¥12,000</span>
                  <span className="text-xs bg-amber-100 text-amber-600 px-2 py-1 rounded">
                    2ヶ月分お得
                  </span>
                </div>
              </div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>受験無制限</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>広告最小化</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✔</span>
                  <span>限定アンケート</span>
                </li>
              </ul>
              <button
                className="w-full py-2 rounded-md border-2 border-amber-500 text-amber-600 hover:bg-amber-50 font-semibold"
                onClick={() => handleUpgrade('pro-yearly')}
              >
                年額で加入
              </button>
            </div>
          </section>

          <section className="space-y-8">
            <h2 className="text-2xl font-bold text-center">Proの特典</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white/70 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold mb-2">受験無制限</h3>
                <p className="text-sm leading-relaxed">
                  Proでは毎日好きなだけテストを受けることができます。学習と
                  成長のサイクルを途切れさせず、最速でスコアを伸ばしましょう。
                </p>
              </div>
              <div className="bg-white/70 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold mb-2">広告最小化</h3>
                <p className="text-sm leading-relaxed">
                  うっとうしい動画広告は最小限に。コンテンツに集中できる
                  静かなテスト体験を提供します。
                </p>
              </div>
              <div className="bg-white/70 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold mb-2">限定アンケート</h3>
                <p className="text-sm leading-relaxed">
                  プロメンバーだけが参加できる特別なアンケートや調査に
                  アクセスできます。参加するとポイントや特典がもらえる
                  こともあります。
                </p>
              </div>
            </div>
          </section>

          <section className="space-y-6">
            <h2 className="text-2xl font-bold text-center">よくある質問</h2>
            <div className="space-y-4 max-w-3xl mx-auto">
              <div>
                <h3 className="font-semibold">いつでも解約できますか？</h3>
                <p className="text-sm leading-relaxed">
                  はい、サブスクリプションはいつでもキャンセルできます。
                  現在の請求期間が終了するまでProの特典をお楽しみください。
                </p>
              </div>
              <div>
                <h3 className="font-semibold">支払い方法は何がありますか？</h3>
                <p className="text-sm leading-relaxed">
                  現在はクレジットカードや暗号資産に対応した決済サービス
                  を準備中です。近日中に追加予定です。
                </p>
              </div>
              <div>
                <h3 className="font-semibold">返金は可能ですか？</h3>
                <p className="text-sm leading-relaxed">
                  ご満足いただけない場合は、購入から7日以内にサポートまで
                  ご連絡ください。個別に対応させていただきます。
                </p>
              </div>
            </div>
          </section>

          <footer className="text-center text-xs text-amber-700 space-y-2">
            <p>
              表示価格はすべて税込です。実際の料金は地域や決済方法によって
              変動する場合があります。
            </p>
            <p>利用規約およびプライバシーポリシーに同意した上でご利用ください。</p>
          </footer>
        </div>
      </div>
    </AppShell>
  );
}
