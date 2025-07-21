import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Layout from '../components/Layout';

export default function DemographicsForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const setId = params.get('set');
  const [age, setAge] = useState('18-29');
  const [gender, setGender] = useState('other');
  const [income, setIncome] = useState('0-3m');

  const save = () => {
    const user = localStorage.getItem('user_id') || 'testuser';
    fetch('/user/demographics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user, age_band: age, gender, income_band: income })
    }).then(() => {
      const path = setId ? `/quiz?set=${setId}` : '/quiz';
      navigate(path);
    });
  };

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto">
      <h2 className="text-xl font-bold">Before you start</h2>
      <div className="form-control">
        <label className="label">Age Range</label>
        <select className="select select-bordered" value={age} onChange={e => setAge(e.target.value)}>
          <option>18-29</option>
          <option>30-49</option>
          <option>50-69</option>
          <option>70+</option>
        </select>
      </div>
      <div className="form-control">
        <label className="label">Gender</label>
        <select className="select select-bordered" value={gender} onChange={e => setGender(e.target.value)}>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="form-control">
        <label className="label">Income</label>
        <select className="select select-bordered" value={income} onChange={e => setIncome(e.target.value)}>
          <option value="0-3m">0-3m JPY</option>
          <option value="3-6m">3-6m JPY</option>
          <option value="6-10m">6-10m JPY</option>
          <option value="10m+">10m+ JPY</option>
        </select>
      </div>
      <button className="btn btn-primary w-full" onClick={save}>Start Quiz</button>
      </div>
    </Layout>
  );
}
