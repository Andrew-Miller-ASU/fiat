import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export default function RecordPage() {
  const [recording, setRecording] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [videoChunks, setVideoChunks] = useState([]);
  const [videoURL, setVideoURL] = useState(null);

  const [analysisType, setAnalysisType] = useState('sit-stand'); // NEW

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

    // Create a File from the in-memory chunks
    const blob = new Blob(videoChunks, { type: 'video/webm' });
    const file = new File([blob], `recorded-video-${Date.now()}.webm`, { type: 'video/webm' });

    const formData = new FormData();
    formData.append('video', file);
    // Pass the chosen analysis type:
    formData.append('analysisType', analysisType);

    try {
      // POST to '/analyze' (instead of '/upload') so we get processed videos
      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      // e.g. data = { original: "myvideo.webm", processed: "myvideo_processed.webm", reps: 3 }
      alert(`
        Upload & Analysis Complete!
        Original: ${data.original}
        Processed: ${data.processed}
        Reps Counted: ${data.reps}
      `);

      // Clear out state so user can record again
      setVideoURL(null);
      setVideoChunks([]);
    } catch (error) {
      console.error('❌ Upload error:', error);
      alert('Error uploading video.');
    }
  }

  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Record Your Video</h2>
      <p>Click "Start Recording" to begin, then "Stop Recording" to finish.</p>

      {/* Choose the type of analysis, similar to UploadPage */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="analysisType">Analysis Type: </label>
        <select
          id="analysisType"
          value={analysisType}
          onChange={(e) => setAnalysisType(e.target.value)}
        >
          <option value="sit-stand">Sit-Stand</option>
          {/* Add more if you want: */}
          {/* <option value="other-type">Other Type</option> */}
        </select>
      </div>

      {/* Live Camera Preview */}
      <video
        ref={videoRef}
        width="400"
        height="300"
        autoPlay
        style={{ backgroundColor: '#000' }}
      />

      <div style={{ marginTop: '20px' }}>
        {!recording ? (
          <button onClick={startRecording}>Start Recording</button>
        ) : (
          <button onClick={stopRecording}>Stop Recording</button>
        )}
      </div>

      {/* Once data is available, let user "Save" the in-memory video to a URL */}
      {videoChunks.length > 0 && !videoURL && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleSaveVideo}>Save Video</button>
        </div>
      )}

      {/* Show local preview once "Save Video" has been clicked */}
      {videoURL && (
        <div style={{ marginTop: '20px' }}>
          <h4>Recorded Video Preview</h4>
          <video src={videoURL} width="400" controls />
          <div style={{ marginTop: '20px' }}>
            <button onClick={handleUpload}>Confirm Upload & Analyze</button>
          </div>
        </div>
      )}

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>
    </div>
  );
}
