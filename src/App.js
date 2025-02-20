import React from "react"; // Importing React to use JSX
import "./App.css"; // Importing CSS for styling

function App() {
  return (
    <div className="App">
      {/* Header Section */}
      <header className="App-header">
        <h1>Frailty Indicator Analysis Tool</h1>
        <p>
          Welcome! This tool will help you assess your frailty by analyzing your sit-stand test. 
          Below is a video that will have instructions on how to perfrom the test.
        </p>
      </header>

      {/* Demo Video Section */}
      <section className="App-demo-video">
        <h2>How to Perform the Test</h2>
        {/* Embed a YouTube video */}
        <iframe
          width="800"
          height="200"
          src="https://www.youtube.com/embed/PzCTwkJVhWg"
          title="Demo Video"
          frameBorder="0"
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      </section>

      {/* Navigation Buttons Section */}
      <section className="App-navigation">
        <h2>Get Started!</h2>
        <div className="nav-buttons">
          <button onClick={() => alert("Upload Video page coming soon!")}>
            Upload a Video
          </button>
          <button onClick={() => alert("Record Video feature coming soon!")}>
            Record a Video
          </button>
          <button onClick={() => alert("View Results page coming soon!")}>
            View Previous Results
          </button>
        </div>
      </section>
    </div>
  );
}

export default App;
