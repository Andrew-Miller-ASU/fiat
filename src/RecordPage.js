import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import "./animations.css"; // for loader_spin CSS
import SitStandScores from "./images/Sit-Stand-Scores.png"; // adjust if needed

const RecordPage = () => {
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [recording, setRecording] = useState(false);
  const [videoBlob, setVideoBlob] = useState(null);
  const [time, setTime] = useState(30);
  const timerRef = useRef(null);
  const [error, setError] = useState("");
  const [webcamAvailable, setWebcamAvailable] = useState(true);
  const [uploadStatus, setUploadStatus] = useState("");
  const [processingResult, setProcessingResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [testConcluded, setTestConcluded] = useState(false);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(() => setWebcamAvailable(true))
        .catch(() => {
          setWebcamAvailable(false);
          setError("No webcam detected. Please connect a webcam to use this feature.");
        });
  }, []);

  const startRecording = () => {
    if (!webcamRef.current || !webcamRef.current.stream) {
      setError("No webcam stream found. Please allow webcam access.");
      return;
    }

    setRecording(true);
    setVideoBlob(null);
    setTime(30);
    setError("");
    setTestConcluded(false);

    timerRef.current = setInterval(() => {
      setTime((prevTime) => {
        if (prevTime === 1) {
          stopRecording();
        }
        return prevTime - 1;
      });
    }, 1000);

    try {
      const stream = webcamRef.current.stream;
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });
      let recordedChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        clearInterval(timerRef.current);
        const blob = new Blob(recordedChunks, { type: "video/webm" });
        setVideoBlob(blob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
    } catch (error) {
      setError("Error initializing recording. Please try again.");
      console.error("Error initializing MediaRecorder:", error);
    }
  };

  const stopRecording = () => {
    setRecording(false);
    clearInterval(timerRef.current);
    if (mediaRecorderRef.current?.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const uploadToServer = async () => {
    if (!videoBlob) {
      setUploadStatus("No video available to upload.");
      return;
    }

    setUploadStatus("Uploading...");
    setIsProcessing(true);
    setTestConcluded(false);

    const formData = new FormData();
    formData.append("video", videoBlob, "sit-stand-test.webm");
    formData.append("analysisType", "sit-stand");

    try {
      const response = await axios.post("http://127.0.0.1:5000/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      if (response.status !== 200) {
        throw new Error(`Server error: ${response.status}`);
      }

      setProcessingResult(response.data);
      setUploadStatus("Processing complete!");
      setIsProcessing(false);
      setTestConcluded(true);
    } catch (error) {
      console.error("Error uploading/analyzing video:", error);
      setUploadStatus("Upload failed. Please try again.");
      setIsProcessing(false);
    }
  };

  const downloadVideo = () => {
    if (videoBlob) {
      const url = URL.createObjectURL(videoBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sit-stand-test.webm";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const loader_animation = () => (
      <div style={{ marginTop: "40px", textAlign: "center" }}>
        <div className="loader_spin" />
        <p>Analysis in progress. This shouldn't take more than a few minutes.</p>
      </div>
  );

  return (
      <div style={{ textAlign: "center", padding: "20px", maxWidth: "1000px", margin: "auto" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "20px" }}>
          Record Your Sit-Stand Test
        </h1>

        {!webcamAvailable && <p style={{ color: "red", fontWeight: "bold" }}>{error}</p>}

        {webcamAvailable && <Webcam ref={webcamRef} />}

        <div>
          {recording ? (
              <>
                <button onClick={stopRecording} style={{ margin: "10px", padding: "10px", backgroundColor: "red", color: "white", border: "none", borderRadius: "5px" }}>
                  Stop
                </button>
                <p>Time Remaining: <strong>{time} seconds</strong></p>
              </>
          ) : (
              <button
                  onClick={startRecording}
                  disabled={!webcamAvailable}
                  style={{
                    margin: "10px",
                    padding: "10px",
                    backgroundColor: webcamAvailable ? "green" : "gray",
                    color: "white",
                    border: "none",
                    borderRadius: "5px",
                    cursor: webcamAvailable ? "pointer" : "not-allowed"
                  }}
              >
                Record
              </button>
          )}
        </div>

        {videoBlob && (
            <div>
              <h3>Review Your Recording:</h3>
              <video src={URL.createObjectURL(videoBlob)} controls style={{ width: "100%", maxWidth: "500px" }} />
              <br />
              <button onClick={downloadVideo} style={{ margin: "10px", padding: "10px", backgroundColor: "black", color: "white", border: "none", borderRadius: "5px" }}>
                Download
              </button>
              <button onClick={uploadToServer} style={{ margin: "10px", padding: "10px", backgroundColor: "blue", color: "white", border: "none", borderRadius: "5px" }}>
                Upload
              </button>
            </div>
        )}

        {isProcessing && loader_animation()}

        {uploadStatus && <p>{uploadStatus}</p>}

        {testConcluded && processingResult && (
            <div style={{ marginTop: "20px" }}>
              {processingResult.success && <p>{processingResult.success}</p>}
              {processingResult.reps && (
                  <p>
                    <strong>Sit-Stand Count:</strong> {processingResult.reps}
                  </p>
              )}
              <img
                  src={SitStandScores}
                  alt="Below Average Scores Based on Age Group"
                  style={{ maxWidth: "100%", marginTop: "20px" }}
              />
            </div>
        )}
      </div>
  );
};

export default RecordPage;
