import React, { useRef } from 'react';
import './FileUpload.css';

function FileUpload({ onFileUpload }) {
  const fileInputRef = useRef(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="file-upload">
      <h2>Upload File</h2>
      <p className="subtitle">CSV or JSON format</p>
      <button className="upload-button" onClick={handleClick}>
        <span className="icon">📁</span>
        Choose File
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.json"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
    </div>
  );
}

export default FileUpload;
