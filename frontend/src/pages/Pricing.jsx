import React from 'react';
import Layout from '../components/Layout';

export default function Pricing() {
  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <h2 className="text-3xl font-bold text-center">Choose Your Plan</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">Free</h3>
            <p className="mb-4">One attempt</p>
            <button className="btn btn-primary" disabled>Current</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">Retry</h3>
            <p className="mb-4">Additional plays</p>
            <button className="btn btn-secondary">Pay with Stripe</button>
          </div>
          <div className="card bg-base-100 shadow-md p-4">
            <h3 className="font-semibold mb-2">Pro Pass</h3>
            <p className="mb-4">Monthly subscription</p>
            <button className="btn btn-primary">Subscribe</button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
