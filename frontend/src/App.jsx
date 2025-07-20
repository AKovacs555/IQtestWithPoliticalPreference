import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

const PageTransition = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {children}
  </motion.div>
);

const Home = () => (
  <PageTransition>
    <div className="p-4 text-center">
      <h1 className="text-2xl font-bold mb-4">IQ Test</h1>
      <Link to="/quiz" className="bg-blue-600 text-white px-4 py-2 rounded">Start Quiz</Link>
    </div>
  </PageTransition>
);

const Quiz = () => (
  <PageTransition>
    <div className="p-4">Quiz goes here.</div>
  </PageTransition>
);

const Result = () => (
  <PageTransition>
    <div className="p-4">Result page.</div>
  </PageTransition>
);

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/quiz" element={<Quiz />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </AnimatePresence>
  );
}
