import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './LandingPage';
import UploadPage from './UploadPage';
import HistoryPage from './HistoryPage';
import RecordPage from './RecordPage';
import LiveProcessingPage from './LiveProcessingPage';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/record" element={<RecordPage />} />
        <Route path="/liveProcessing" element={<LiveProcessingPage />} />
      </Routes>
    </Router>
  );
}
