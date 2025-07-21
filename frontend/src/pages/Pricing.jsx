import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';

const userId = 'demo';

export default function Pricing() {
  const { t } = useTranslation();
  const [price, setPrice] = useState(0);
  const [proPrice, setProPrice] = useState(0);

  useEffect(() => {
    fetch(`/pricing/${userId}`)
      .then(res => res.json())
      .then(data => {
        setPrice(data.price);
        setProPrice(data.pro_price);
      });
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <h2 className="text-3xl font-bold text-center">{t('pricing.title')}</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.free')}</h3>
            <p className="mb-4">1</p>
            <button className="btn btn-primary" disabled>Current</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.retry')}</h3>
            <p className="mb-4">{price} JPY</p>
            <button className="btn btn-secondary">Pay with Stripe</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">{t('pricing.subscribe')}</h3>
            <p className="mb-4">{proPrice} JPY / mo</p>
            <button className="btn btn-primary">Subscribe</button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
