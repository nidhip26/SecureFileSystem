import { useEffect, useState } from 'react';
// import './SecureFileSharingGUI.css';
import './SecureFileSharingGUI.css';

import { useNavigate } from 'react-router-dom';

export default function SecureFileSharingGUI({ username, onLogout }) {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/users')
      .then(res => res.json())
      .then(data => {
        const otherUsers = data.filter(u => u.username !== username);
        setUsers(otherUsers);
        if (otherUsers.length > 0) {
          setSelectedUser(otherUsers[0].username); // auto-select first user
        }
      })
      .catch(err => console.error('Error fetching users:', err));
  }, [username]);

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('sender_username', username);
    formData.append('recipient_username', selectedUser);

    fetch('http://127.0.0.1:5000/upload', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        const uploaded = {
          name: file.name,
          uploadedAt: new Date().toLocaleString(),
          sharedWith: selectedUser
        };
        setUploadedFiles(prev => [...prev, uploaded]);
      })
      .catch(err => console.error('Error uploading file:', err));
  };

  const handleDownload = (fileName) => {
    alert(`Simulating download for: ${fileName}`);
    // In a real app, you'd initiate the file download here.
  };

  const getAvatar = (name) => {
    if (typeof name !== 'string') {
      return '❓';
    }

    const emojis = ['🧑‍💻', '👨‍🔧', '👩‍🎨', '🧑‍🚀', '👨‍🍳', '🧙‍♂️'];
    const hash = [...name].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    return emojis[hash % emojis.length];
  };

  return (
    <>
    <nav className="navbar">
        <span>Logged in as <strong>{username}</strong></span>
        <div>
          <button className="nav-button" onClick={() => navigate('/Files')}>My Files</button>
          <button className="nav-button" onClick={handleLogout}>Logout</button>
        </div>
      </nav>
    <div className="container">

      {/* Sidebar with tabs */}
      <div className="sidebar">
        {users.map((user, index) => (
          <button
            key={index}
            className={`avatar ${selectedUser === user.username ? 'selected' : ''}`}
            onClick={() => setSelectedUser(user.username)}
            title={user.username}
          >
            {getAvatar(user.username)}
          </button>
        ))}
      </div>

      {/* Main Panel */}
      <div className="main-panel">
        {selectedUser ? (
          <>
            <h1 className="welcome">Share with {selectedUser}</h1>

            {/* Upload section */}
            <div className="upload-box">
              <input
                type="file"
                className="file-input"
                onChange={handleUpload}
              />
              {/* <button className="upload-button">Upload</button> */}
            </div>

            {/* Uploaded Files */}
            <div className="file-list">
              {uploadedFiles
                .filter(file => file.sharedWith === selectedUser)
                .map((file, index) => (
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
          </>
        ) : (
          <p className="no-users">No users to share with.</p>
        )}
      </div>
    </div>
    </>
  );

  // useEffect(() => {
  //   fetch('http://127.0.0.1:5000/users')
  //     .then(res => res.json())
  //     .then(data => {
  //       const otherUsers = data.filter(u => u.username !== username);
  //       setUsers(otherUsers);
  //       if (otherUsers.length > 0) {
  //         setSelectedUser(otherUsers[0].username); // auto-select first user
  //       }
  //     })
  //     .catch(err => console.error('Error fetching users:', err));
  // }, [username]);



  // const handleLogout = () => {
  //   onLogout();
  //   navigate('/login');
  // };

  // const handleUpload = (event) => {
  //   const file = event.target.files[0];
  //   if (!file) return;
  
  //   const formData = new FormData();
  //   formData.append('file', file);
  //   formData.append('sender_username', username); 
  //   formData.append('recipient_username', selectedUser);
  
  //   fetch('http://127.0.0.1:5000/upload', {
  //     method: 'POST',
  //     body: formData
  //   })
  //     .then(res => res.json())
  //     .then(data => {
  //       const uploaded = {
  //         name: file.name,
  //         uploadedAt: new Date().toLocaleString(),
  //         sharedWith: selectedUser
  //       };
  //       setUploadedFiles(prev => [...prev, uploaded]);
  //     })
  //     .catch(err => console.error('Error uploading file:', err));
  // };
  

  // const handleDownload = (fileName) => {
  //   alert(`Simulating download for: ${fileName}`);
  //   // In a real app, you'd initiate the file download here.
  // };

  // const getAvatar = (name) => {
  //   if (typeof name !== 'string') {
  //     return '❓';
  //   }

  //   const emojis = ['🧑‍💻', '👨‍🔧', '👩‍🎨', '🧑‍🚀', '👨‍🍳', '🧙‍♂️'];
  //   const hash = [...name].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  //   return emojis[hash % emojis.length];
  // };

  // return (
  //   <div className="container">
  //     <nav style={{ display: "flex", justifyContent: "space-between", padding: "10px", background: "#eee" }}>
  //       <span>Logged in as <strong>{username}</strong></span>
  //       <div>
  //       <button onClick={() => navigate('/Files')} style={{ marginRight: '10px' }}>  My Files</button>

  //         <button onClick={handleLogout}>Logout</button>
  //       </div>
  //     </nav>

  //     {/* Sidebar with tabs */}
  //     <div className="sidebar">
  //       {users.map((user, index) => (
  //         <button
  //           key={index}
  //           className={`avatar ${selectedUser === user.username ? 'selected' : ''}`}
  //           onClick={() => setSelectedUser(user.username)}
  //           title={user.username}
  //         >
  //           {getAvatar(user.username)}
  //         </button>
  //       ))}
  //     </div>

  //     {/* Main Panel */}
  //     <div className="main-panel">
  //       {selectedUser ? (
  //         <>
  //           <h1 className="welcome">Share with {selectedUser}</h1>

  //           {/* Upload section */}
  //           <div className="upload-box">
  //             <input
  //               type="file"
  //               className="file-input"
  //               onChange={handleUpload}
  //             />
  //             <button className="upload-button">Upload</button>
  //           </div>

  //           {/* Uploaded Files */}
  //           <div className="file-list">
  //             {uploadedFiles
  //               .filter(file => file.sharedWith === selectedUser)
  //               .map((file, index) => (
  //                 <div key={index} className="file-entry">
  //                   <div>
  //                     <div className="file-name">{file.name}</div>
  //                     <div className="file-time">Uploaded at: {file.uploadedAt}</div>
  //                   </div>
  //                   <button
  //                     onClick={() => handleDownload(file.name)}
  //                     className="download-button"
  //                   >
  //                     Download
  //                   </button>
  //                 </div>
  //               ))}
  //           </div>
  //         </>
  //       ) : (
  //         <p style={{ padding: '20px' }}>No users to share with.</p>
  //       )}
  //     </div>
  //   </div>
  // );
}