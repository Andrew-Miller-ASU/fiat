import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import scores from './images/Sit-Stand-Scores.png';
import './animations.css';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewURL, setPreviewURL] = useState(null);
  const [analysisType, setAnalysisType] = useState('sit-stand');
  const fileInputRef = useRef(null);
  const [data, setData] = useState('');
  
  const [testConcluded, setTestConcluded] = useState(false);
  const [testStarted, setTestStarted] = useState(false);

   
  function handleFileChange(event) {
    const file = event.target.files[0];
    setSelectedFile(null);
    setPreviewURL(null);
    if (!file) {
      //setSelectedFile(null);
      //setPreviewURL(null);
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
    setTestConcluded(false);
    setTestStarted(true);
    const formData = new FormData();
    formData.append('video', selectedFile);
    // Optional: pass an analysisType if your server code expects it:
    formData.append('analysisType', analysisType);
      //Canvas();
    try {
      // POST to your new '/analyze' endpoint (instead of '/upload')
      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }


        setData(await response.json()); // This will be your output
        


      

      // Clear UI
      setSelectedFile(null);
      setPreviewURL(null);
      setTestConcluded(true);
      setTestStarted(false);

    } catch (error) {
      console.error('Error uploading/analyzing video:', error);
      alert('Error uploading video. Check console for details.');
    }
  }

  function handleClickChooseFile() {
    fileInputRef.current.click();
  }

    const loader_animation = () => {

        return <div className="loader_spin"></div>
    };

    

  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Upload & Analyze Your Video</h2>
      <p>Select a video file to be processed.</p>

      {/* Analysis selection (currently just one type, but you could add more) */}
      <label htmlFor="analysisSelect">Choose Analysis Type:</label>
      <select
        id="analysisSelect"
        value={analysisType}
        onChange={(e) => setAnalysisType(e.target.value)}
        style={{ marginLeft: '10px', marginRight: '20px' }}
      >
        <option value="sit-stand">Sit-Stand</option>
        {/* Add other analysis types here */}
      </select>

      <button onClick={handleClickChooseFile}>Choose Video</button>
      <input
        type="file"
        accept="video/*"
        style={{ display: 'none' }}
        ref={fileInputRef}
        onChange={handleFileChange}
      />

      {previewURL && !testStarted && (
        <div style={{ marginTop: '20px' }}>
          <h4>Preview:</h4>
          <video src={previewURL} width="400" controls />
        </div>
      )}

      {previewURL && !testStarted && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleConfirmUpload}>Confirm Upload</button>
        </div>
      )}

          

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>

      { testStarted && (

              <div style={{ textAlign: 'center', marginTop: '60px' }}>
                  {loader_animation()}
                  Analysis in progress. This shouldn't take more than a few minutes.
              </div>

      )}
          
          

          <p>   {/* Output Results */}
              { testConcluded && (
                  <div>
                    <br/>
                    {data.success}
                    
                    <br/><br/>
                    <b>{data.reps}</b>
                </div>
              )}
      </p>
      {testConcluded && (

          <img src={scores} alt="Below Average Scores Based on Age Group" /> 

      )} {/* Scores image */}
    </div>
  );
}
