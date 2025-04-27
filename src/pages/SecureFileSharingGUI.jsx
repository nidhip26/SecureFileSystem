import { useState } from 'react';
import './SecureFileSharingGUI.css';

const demoUsers = [
  { id: 1, name: 'Alice', avatar: '🧑‍💻' },
  { id: 2, name: 'Bob', avatar: '👨‍🔧' },
  { id: 3, name: 'Charlie', avatar: '👩‍🎨' }
];

export default function SecureFileSharingGUI() {
  const [selectedUser, setSelectedUser] = useState(demoUsers[0]);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleUpload = (event) => {
    const files = Array.from(event.target.files);
    const newFiles = files.map(file => ({
      name: file.name,
      uploadedAt: new Date().toLocaleString()
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleDownload = (fileName) => {
    alert(`Simulating download for: ${fileName}`);
  };

  return (
    <div className="container">
      {/* Sidebar */}
      <div className="sidebar">
        {demoUsers.map(user => (
          <button
            key={user.id}
            className={`avatar ${selectedUser.id === user.id ? 'selected' : ''}`}
            onClick={() => setSelectedUser(user)}
          >
            {user.avatar}
          </button>
        ))}
      </div>

      {/* Main Panel */}
      <div className="main-panel">
        <h1 className="welcome">Welcome, {selectedUser.name}</h1>

        {/* Upload Section */}
        <div className="upload-box">
          <input
            type="file"
            multiple
            className="file-input"
            onChange={handleUpload}
          />
          <button className="upload-button">Upload</button>
        </div>

        {/* Uploaded Files */}
        <div className="file-list">
          {uploadedFiles.map((file, index) => (
            <div key={index} className="file-entry">
              <div>
                <div className="file-name">{file.name}</div>
                <div className="file-time">Uploaded at: {file.uploadedAt}</div>
              </div>
              <button
                onClick={() => handleDownload(file.name)}
                className="download-button"
              >
                Download
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}