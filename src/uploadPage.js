import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import scores from './images/Sit-Stand-Scores.png';
import io from 'socket.io-client';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewURL, setPreviewURL] = useState(null);
  const [analysisType, setAnalysisType] = useState('sit-stand');
  const fileInputRef = useRef(null);
  const [data, setData] = useState('');
  const canvasRef = useRef(null);

    function Canvas() {


       // useEffect(() => {
            const canvas = canvasRef.current;
            const context = canvas.getContext('2d');

            // Example drawing: a blue rectangle
            //context.fillStyle = 'lightblue';
            context.fillRect(30, 30, 400, 400);
       // context.drawImage(fileInputRef.current, 0, 0, canvas.width, canvas.height);

            // Example drawing: a red circle
            //context.beginPath();
            //context.arc(300, 70, 50, 0, 2 * Math.PI);
            //context.fillStyle = 'red';
            //context.fill();
            //context.closePath();

            // Example drawing: text
            //context.font = '20px Arial';
            //context.fillStyle = 'black';
            //context.fillText('Hello, Canvas!', 50, 150);

        //}, []);

        
    }
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


      //const data = await response.json();
      // e.g. data = { original: "myvideo.mp4", processed: "myvideo_processed.mp4", reps: 3 }
      /*alert(
        `Upload & Analysis Complete!
         Original: ${data.original}
         Processed: ${data.processed}
         Reps Counted: ${data.reps}`
      );*/

      // Clear UI
      setSelectedFile(null);
      setPreviewURL(null);
    } catch (error) {
      console.error('Error uploading/analyzing video:', error);
      alert('Error uploading video. Check console for details.');
    }
  }

  function handleClickChooseFile() {
    fileInputRef.current.click();
  }

    

    

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

      {previewURL && (
        <div style={{ marginTop: '20px' }}>
          <h4>Preview:</h4>
          <video src={previewURL} width="400" controls />
        </div>
      )}

      {previewURL && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleConfirmUpload}>Confirm Upload</button>
        </div>
      )}

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>
          {/*Canvas()*/}
          {/*<canvas ref={canvasRef} width={800} height={800} /> */}
          

      <p>   {/* Output Results */}
                <br/>
                {data.success}
                <br/><br/>
                {data.original}
                <br/><br/>
                {data.processed}
                <br/><br/>
                {data.reps}
      </p>
      <img src={scores} alt="Below Average Scores Based on Age Group" /> {/* Scores image */}
    </div>
  );
}
