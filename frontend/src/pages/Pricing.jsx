import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { useTranslation } from 'react-i18next';
import AdProgress from '../components/AdProgress';
import UpgradeTeaser from '../components/home/UpgradeTeaser';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const userId = 'demo';

export default function Pricing() {
  const { t } = useTranslation();
  const [price, setPrice] = useState(0);
  const [proPrice, setProPrice] = useState(0);
  const [progress, setProgress] = useState(0);
  const [crypto, setCrypto] = useState('usdt');
  const [freeAttempts, setFreeAttempts] = useState(0);

  const watchAd = () => {
    setProgress(0);
    fetch(`${API_BASE}/ads/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    const id = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(id);
          fetch(`${API_BASE}/ads/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
          });
          return 100;
        }
        return p + 10;
      });
    }, 300);
  };

  useEffect(() => {
    fetch(`${API_BASE}/pricing/${userId}`)
      .then(res => {
        if (!res.ok) throw new Error('pricing');
        return res.json();
      })
      .then(data => {
        setPrice(data?.retry?.amount_minor ?? 0);
        setProPrice(data?.pro_pass?.amount_minor ?? 0);
        setFreeAttempts(0);
      })
      .catch(() => {
        setPrice(0);
        setProPrice(0);
        setFreeAttempts(0);
      });
  }, []);

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <h2 className="text-3xl font-bold text-center">{t('pricing.title')}</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="relative glass-card gold-ring gold-sheen p-4 shadow-sm opacity-60">
            <h3 className="font-semibold mb-2">{t('pricing.free')}</h3>
            <p className="mb-4">{freeAttempts}</p>
            <button disabled className="w-full py-2 rounded-md bg-gray-600 text-gray-400 cursor-not-allowed">
              現在のプラン
            </button>
          </div>
          <div className="relative glass-card gold-ring gold-sheen p-4 shadow-sm">
            <h3 className="font-semibold mb-2">{t('pricing.retry')}</h3>
            <p className="mb-4">{price} JPY</p>
            <select
              className="w-full border rounded-md px-3 py-2 mb-2"
              value={crypto}
              onChange={e => setCrypto(e.target.value)}
            >
              <option value="sol">SOL</option>
              <option value="xrp">XRP</option>
              <option value="trx">TRX</option>
              <option value="usdttrc20">USDT</option>
              <option value="eth">ETH</option>
              <option value="bnb">BNB</option>
            </select>
            <button
              className="w-full py-2 rounded-md border-2 border-amber-400 text-amber-400 hover:bg-amber-500/10 font-semibold"
              onClick={() => {
                fetch(`${API_BASE}/purchase`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ user_id: userId, amount: price, pay_currency: crypto })
                })
                  .then(res => res.json())
                  .then(data => {
                    if (data.payment_url) window.location = data.payment_url;
                  });
              }}
            >
              Pay with Crypto
            </button>
          </div>
          <div className="relative glass-card gold-ring gold-sheen p-4 shadow-md border-2 border-amber-400">
            <h3 className="font-semibold mb-2">{t('pricing.subscribe')}</h3>
            <p className="mb-4">{proPrice} JPY / mo</p>
            <button className="w-full py-2 rounded-md bg-amber-500 hover:bg-amber-600 hover:shadow-lg hover:shadow-amber-500/50 text-white font-semibold">
              アップグレード
            </button>
          </div>
        </div>
        <UpgradeTeaser />
        <div className="text-center space-y-2">
          <button
            onClick={watchAd}
            className="px-4 py-2 rounded-md bg-accent text-white"
          >
            Watch Ad
          </button>
          {progress > 0 && progress < 100 && <AdProgress progress={progress} />}
        </div>
      </div>
    </AppShell>
  );
}

