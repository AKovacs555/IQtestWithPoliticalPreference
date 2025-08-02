import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';
import AdProgress from '../components/AdProgress';

const API_BASE = import.meta.env.VITE_API_BASE || "";

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
    fetch(`${API_BASE}/ads/start`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ user_id: userId }) });
    const id = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(id);
          fetch(`${API_BASE}/ads/complete`, { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: userId }) });
          return 100;
        }
        return p + 10;
      });
    }, 300);
  };

  useEffect(() => {
    fetch(`${API_BASE}/pricing/${userId}`)
      .then(res => res.json())
      .then(data => {
        setPrice(data.price);
        setProPrice(data.pro_price);
        setFreeAttempts(data.free_attempts ?? 0);
      });
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <h2 className="text-3xl font-bold text-center">{t('pricing.title')}</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.free')}</h3>
            <p className="mb-4">{freeAttempts}</p>
            <button className="btn btn-primary" disabled>Current</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.retry')}</h3>
            <p className="mb-4">{price} JPY</p>
            <select className="select select-bordered w-full mb-2" value={crypto} onChange={e => setCrypto(e.target.value)}>
              <option value="sol">SOL</option>
              <option value="xrp">XRP</option>
              <option value="trx">TRX</option>
              <option value="usdttrc20">USDT</option>
              <option value="eth">ETH</option>
              <option value="bnb">BNB</option>
            </select>
            <button className="btn btn-secondary" onClick={() => {
              fetch(`${API_BASE}/purchase`, { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: userId, amount: price, pay_currency: crypto }) })
                .then(res => res.json())
                .then(data => { if (data.payment_url) window.location = data.payment_url; });
            }}>Pay with Crypto</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.subscribe')}</h3>
            <p className="mb-4">{proPrice} JPY / mo</p>
            <button className="btn btn-primary">Subscribe</button>
          </div>
        </div>
        <div className="text-center space-y-2">
          <button onClick={watchAd} className="btn btn-accent">Watch Ad</button>
          {progress > 0 && progress < 100 && <AdProgress progress={progress} />}
        </div>
      </div>
    </Layout>
  );
}
