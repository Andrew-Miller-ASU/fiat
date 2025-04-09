import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export default function RecordPage() {
  const [recording, setRecording] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [videoChunks, setVideoChunks] = useState([]);
  const [videoURL, setVideoURL] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisType, setAnalysisType] = useState('sit-stand');

  const videoRef = useRef(null);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setMediaStream(stream);
      videoRef.current.srcObject = stream;

      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setVideoChunks((prev) => [...prev, event.data]);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (error) {
      console.error('Error accessing camera/mic:', error);
      alert('Could not access camera or microphone.');
    }
  }

  function stopRecording() {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setRecording(false);
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
    }
  }

  function handleSaveVideo() {
    if (videoChunks.length) {
      const blob = new Blob(videoChunks, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      setVideoURL(url);
    }
  }

  async function handleUpload() {
    if (!videoURL) {
      alert('No recorded video to upload.');
      return;
    }

    const blob = new Blob(videoChunks, { type: 'video/webm' });
    const file = new File([blob], `recorded-video-${Date.now()}.webm`, { type: 'video/webm' });

    const formData = new FormData();
    formData.append('video', file);
    formData.append('analysisType', analysisType);

    try {
      setLoading(true);

      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      if (data.warning) {
        alert(`Warning: ${data.warning}`);
      } else {
      alert(`
        Upload & Analysis Complete!
        Original: ${data.original}
        Processed: ${data.processed}
        Reps Counted: ${data.reps}
      `);
      }

      setVideoURL(null);
      setVideoChunks([]);
    } catch (error) {
      console.error(' Upload error:', error);
      alert('Error uploading video.');
    } finally {
      setLoading(false);
    }
  }

  
  
  
  
  
  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Record Your Video</h2>
      <p>Click "Start Recording" to begin, then "Stop Recording" to finish.</p>

      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="analysisType">Analysis Type: </label>
        <select
          id="analysisType"
          value={analysisType}
          onChange={(e) => setAnalysisType(e.target.value)}
          disabled={loading}
        >
          <option value="sit-stand">Sit-Stand</option>
        </select>
      </div>

      <video
        ref={videoRef}
        width="400"
        height="300"
        autoPlay
        style={{ backgroundColor: '#000' }}
      />

      <div style={{ marginTop: '20px' }}>
        {!recording ? (
          <button onClick={startRecording} disabled={loading}>Start Recording</button>
        ) : (
          <button onClick={stopRecording}>Stop Recording</button>
        )}
      </div>

      {videoChunks.length > 0 && !videoURL && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleSaveVideo} disabled={loading}>Save Video</button>
        </div>
      )}

      {videoURL && (
        <div style={{ marginTop: '20px' }}>
          <h4>Recorded Video Preview</h4>
          <video src={videoURL} width="400" controls />
          <div style={{ marginTop: '20px' }}>
            <button onClick={handleUpload} disabled={loading}>Confirm Upload & Analyze</button>
          </div>
        </div>
      )}

      {loading && (
        <div style={{ marginTop: '20px' }}>
          <div className="loader" />
          <p>Processing video... please wait.</p>
        </div>
      )}

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button disabled={loading}>Back to Main</button>
        </Link>
      </div>
    </div>
  );
}
