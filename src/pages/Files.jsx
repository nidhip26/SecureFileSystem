import { useEffect, useState } from 'react';
import axios from 'axios';
import './files.css';

export default function Files() {
  const username = localStorage.getItem('username');
  const password = localStorage.getItem('password');
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
    
    let storedPassword = localStorage.getItem('password');
    
    // Show prompt if password is not stored or is empty
    if (storedPassword === null || storedPassword.trim() === '') {
      storedPassword = prompt("Enter your password to decrypt:");
      if (!storedPassword) {
        alert("Password is required to download.");
        return;
      }
      // Optional: save for this session
      localStorage.setItem('password', storedPassword);
    }
    
    try {
      console.log("Sending download request with credentials:", {
        username,
        password: "***" // Don't log actual password
      });
      
      // First attempt with JSON
      const response = await axios({
        method: 'post',
        url: `http://127.0.0.1:5000/download/${selectedFile.id}`,
        data: {
          username,
          password: storedPassword
        },
        headers: { 
          'Content-Type': 'application/json',
          'Accept': '*/*'
        },
        responseType: 'blob'
      });
      
      console.log("Download response received:", response.status);
      
      // Check if we got a JSON error response
      if (response.data.type === 'application/json') {
        // Convert blob to text
        const text = await response.data.text();
        const error = JSON.parse(text);
        throw new Error(error.error || 'Unknown error');
      }
      
      // Create download link
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
      
      if (err.response) {
        // Server responded with an error
        console.error('Server error:', err.response.status, err.response.data);
        
        // Try to extract error message
        let errorMsg = 'Failed to download and decrypt file.';
        if (err.response.data instanceof Blob) {
          try {
            const text = await err.response.data.text();
            const errorObj = JSON.parse(text);
            errorMsg = errorObj.error || errorMsg;
          } catch (e) {
            console.error('Error parsing error response:', e);
          }
        }
        
        alert(errorMsg);
      } else {
        alert('Failed to download and decrypt file. Network error or server unavailable.');
      }
    }
  };
  
  
  

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar */}
      <div style={{
        width: '250px',
        backgroundColor: '#f4f4f4',
        padding: '1rem',
        borderRight: '1px solid #ccc',
        overflowY: 'auto'
      }}>
        <h3>My Files</h3>
        {files.map(file => (
          <button
            key={file.id}
            onClick={() => setSelectedFile(file)}
            style={{
              display: 'block',
              width: '100%',
              marginBottom: '0.5rem',
              padding: '0.5rem',
              backgroundColor: selectedFile?.id === file.id ? '#ddd' : '#fff',
              border: '1px solid #ccc',
              cursor: 'pointer'
            }}
          >
            {file.filename}
          </button>
        ))}
      </div>

      {/* File Preview */}
      <div style={{ flex: 1, padding: '1rem' }}>
        {selectedFile ? (
          <>
            <h2>{selectedFile.filename}</h2>
            <p><strong>MIME Type:</strong> {selectedFile.mime_type}</p>
            <p><strong>Size:</strong> {selectedFile.size} bytes</p>
            <p><strong>Contents:</strong></p>
            <div style={{ background: '#eee', padding: '1rem' }}>
              <pre>
                This is pseudo content for: {selectedFile.filename}
              </pre>
            </div>
            <button
              onClick={handleDownload}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Download & Decrypt
            </button>
          </>
        ) : (
          <p>Select a file from the sidebar to view its details.</p>
        )}
      </div>
    </div>
  );
}
