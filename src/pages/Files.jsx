import { useEffect, useState } from 'react';
import axios from 'axios';
import './files.css';

export default function Files() {
  const username = localStorage.getItem('username');
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    axios
      .get(`http://127.0.0.1:5000/files?username=${username}`)
      .then(res => setFiles(res.data))
      .catch(err => console.error(err));
  }, [username]);

  
  const handleDownload = async () => {
    if (!selectedFile) return;
  
    const inputPassword = prompt("Enter your password to decrypt:");
    if (!inputPassword) {
      alert("Password is required to download.");
      return;
    }
  
    try {
      console.log("Sending download request...");
  
      const response = await axios({
        method: 'post',
        url: `http://127.0.0.1:5000/download/${selectedFile.id}`,
        data: {
          username,
          password: inputPassword
        },
        headers: { 
          'Content-Type': 'application/json',
          'Accept': '*/*'
        },
        responseType: 'blob'
      });
  
      console.log("Download response received:", response.status);
  
      // Check if blob is actually an error JSON
      const contentType = response.headers['content-type'];
      if (contentType && contentType.includes('application/json')) {
        const text = await response.data.text();
        const error = JSON.parse(text);
        throw new Error(error.error || 'Unknown error');
      }
  
      // Create a download link
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = selectedFile.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
  
    } catch (err) {
      console.error('Error downloading file:', err);
  
      let errorMsg = 'Failed to download and decrypt file.';
      try {
        if (err.response?.data instanceof Blob) {
          const text = await err.response.data.text();
          const errorObj = JSON.parse(text);
          errorMsg = errorObj.error || errorMsg;
        }
      } catch (e) {
        console.error('Error parsing error response:', e);
      }
  
      alert(errorMsg);
    }
  };
  
  
  const handleRawDownload = async () => {
    if (!selectedFile) return;
  
    try {
      console.log("Sending raw download request...");
  
      const response = await axios({
        method: 'post',
        url: `http://127.0.0.1:5000/download_raw/${selectedFile.id}`,
        data: { username },
        headers: {
          'Content-Type': 'application/json',
          'Accept': '*/*'
        },
        responseType: 'blob'
      });
  
      console.log("Raw download response received:", response.status);
  
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = selectedFile.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
  
    } catch (err) {
      console.error('Error downloading raw file:', err);
      alert('Failed to download encrypted file.');
    }
  };
  
  

  return (
    <>
    <nav className="navbar">
      <span>Logged in as <strong>{username}</strong></span>
      <div>
        <button className="nav-button" onClick={() => window.location.href = '/'}>Back to Share</button>
        <button className="nav-button" onClick={() => {
          localStorage.removeItem('username');
          window.location.href = '/login';
        }}>
          Logout
        </button>
      </div>
    </nav>

    <div className="files-container">
  <div className="files-sidebar">
    <h3>My Files</h3>
    {files.map(file => (
      <button
        key={file.id}
        onClick={() => setSelectedFile(file)}
        className={`file-button ${selectedFile?.id === file.id ? 'selected' : ''}`}
      >
        {file.filename}
      </button>
    ))}
  </div>

  <div className="file-preview">
    {selectedFile ? (
      <>
        <h2>{selectedFile.filename}</h2>
        <p><strong>MIME Type:</strong> {selectedFile.mime_type}</p>
        <p><strong>Size:</strong> {selectedFile.size} bytes</p>
        <p><strong>Contents:</strong></p>
        <div className="preview-box">
          <pre>This is pseudo content for: {selectedFile.filename}</pre>
        </div>
        <button onClick={handleDownload} className="download-button">
          Download & Decrypt
        </button>
        <button onClick={handleRawDownload} className="download-button">
          Download Encrypted
        </button>

      </>
    ) : (
      <p>Select a file from the sidebar to view its details.</p>
    )}
  </div>
</div>
</>

  );
}
