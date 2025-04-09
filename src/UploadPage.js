import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import scores from './images/Sit-Stand-Scores.png';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewURL, setPreviewURL] = useState(null);
  const [analysisType, setAnalysisType] = useState('sit-stand');
  const fileInputRef = useRef(null);
  const [data, setData] = useState('');
  const [loading, setLoading] = useState(false); // just one loading flag

  function handleFileChange(event) {
    const file = event.target.files[0];
    if (!file) {
      setSelectedFile(null);
      setPreviewURL(null);
      return;
    }
    setSelectedFile(file);
    setPreviewURL(URL.createObjectURL(file));
  }

  async function handleConfirmUpload() {
    if (!selectedFile) {
      alert('No file selected!');
      return;
    }

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('analysisType', analysisType);

    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const json = await response.json();
      setData(json);
      setSelectedFile(null);
      setPreviewURL(null);
    } catch (error) {
      console.error('Error uploading/analyzing video:', error);
      alert('Error uploading video. Check console for details.');
    } finally {
      setLoading(false);
    }
  }

  function handleClickChooseFile() {
    fileInputRef.current.click();
  }

  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Upload & Analyze Your Video</h2>
      <p>Select a video file to be processed.</p>

      <label htmlFor="analysisSelect">Choose Analysis Type:</label>
      <select
        id="analysisSelect"
        value={analysisType}
        onChange={(e) => setAnalysisType(e.target.value)}
        style={{ marginLeft: '10px', marginRight: '20px' }}
        disabled={loading}
      >
        <option value="sit-stand">Sit-Stand</option>
      </select>

      <button onClick={handleClickChooseFile} disabled={loading}>Choose Video</button>
      <input
        type="file"
        accept="video/*"
        style={{ display: 'none' }}
        ref={fileInputRef}
        onChange={handleFileChange}
      />

      {previewURL && (
        <div style={{ marginTop: '20px' }}>
          <h4>Preview:</h4>
          <video src={previewURL} width="400" controls />
        </div>
      )}

      {previewURL && !loading && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleConfirmUpload}>Confirm Upload</button>
        </div>
      )}

      {/* 🌀 Loading Spinner */}
      {loading && (
        <div style={{ marginTop: '20px' }}>
          <div className="loader" />
          <p>Processing video... please wait.</p>
        </div>
      )}

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>

      <p>
        <br />
        {data.success}
        <br /><br />
        {data.original}
        <br /><br />
        {data.processed}
        <br /><br />
        {data.reps}
      </p>

      <img src={scores} alt="Below Average Scores Based on Age Group" />
    </div>
  );
}
