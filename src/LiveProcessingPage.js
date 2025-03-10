import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import scores from './images/Sit-Stand-Scores.png';

function MyLiveProcessPage() {

    
    const [data, setData] = useState('');
    async function handleClick(){

        
        try {
            const response = await fetch('http://127.0.0.1:5000/live_analyze', { // Make an Http POST request to http://localhost:5000/live_record

                

            }) /*.then(

                res => res.text()
            ).then(

                text => setData(text)
            )*/

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            setData(await response.json());
        }
        catch (error) {

            console.error('Fetch error:', error);
        }
    };



    return (
        <div style={{ textAlign: 'center', marginTop: '60px' }}>

            <h2>
                Live Processing
            </h2>
            <p>
                 1. Click the "Live Record" button. <br/><br/>
                 2. Wait for the Frailty Indicator Analysis Tool to access your webcam. <br/><br/>
                 3. Perform sit-stand test. <br/><br/>
                 Make sure that you are far enough away from the camera. <br />
                 Your whole body should be visible from head to toe. <br />
                 The timer will begin when you sit down in the chair. <br />
            </p>
            <button onClick={handleClick}>
                Live Record
            </button>


            <br />
            

            <div style={{ marginTop: '30px' }}>
                <Link to="/">
                    <button>Back to Main</button>
                </Link>
            </div>
            <p>
                <br/>
                {data.success}
                <br/><br/>
                {data.original}
                <br/><br/>
                {data.processed}
                <br/><br/>
                {data.reps}
            </p>
            <img src={scores} alt="Below Average Scores Based on Age Group"/>
            
        </div>


    );
}


export default MyLiveProcessPage;