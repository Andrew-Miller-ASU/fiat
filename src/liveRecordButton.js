
import React, { useState, useRef } from 'react';
// Make sure Proxy is properly set in package.json! In this case, I used http://localhost:5000
function MyLiveRecordButton() {

    //const [selectedVideo, setSelectedVideo] = useState(null);
    //const fileInputRef = useRef(null);
    const [data, setData] = useState('');

   /* const handleFileChange = async (event) => {
    //    const file = event.target.files[0];

    //    if (file) {
        //    setSelectedVideo(URL.createObjectURL(file));

            //const formData = new FormData();
          //  formData.append('video', file);
            try {
                const response = await fetch('/live_record', { // Make an Http POST request to http://localhost:5000/upload

                    //method: 'POST',
                    //body: formData,

                }).then(

                    res => res.text()
                ).then(

                    text => setData(text) //console.log(text)

                )

            }
            catch (error) {

                console.error('Fetch error:', error);
            }
      //  }
      





    };*/



    const handleClick = () => {

        //  fileInputRef.current.click();
        try {
            const response = fetch('/live_record', { // Make an Http POST request to http://localhost:5000/upload

                //method: 'POST',
                //body: formData,

            }).then(

                res => res.text()
            ).then(

                text => setData(text) //console.log(text)

            )

        }
        catch (error) {

            console.error('Fetch error:', error);
        }
    };



    return (
        <div>
            <button onClick={handleClick}>
                Live Record
            </button>
            
            
            <br />
            <br />
            {data}

        </div>

    );
}


export default MyLiveRecordButton;