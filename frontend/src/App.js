import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import FileUpload from './components/FileUpload';
import MappingInterface from './components/MappingInterface';
import Stats from './components/Stats';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function App() {
  const [progress, setProgress] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [categoriesRes, progressRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/categories`),
        axios.get(`${API_BASE_URL}/progress`)
      ]);
      setCategories(categoriesRes.data.categories);
      setProgress(progressRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to load data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API_BASE_URL}/upload`, formData);
      setProgress(res.data.progress);
      setError(null);
    } catch (err) {
      console.error('Upload error:', err);
      let errorMsg = 'Failed to upload file: ' + err.message;
      if (err.response) {
        console.error('Response data:', err.response.data);
        errorMsg = 'Upload error: ' + JSON.stringify(err.response.data);
      }
      setError(errorMsg);
    }
  };

  const handleMapRow = async (rowIndex, category) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/map-row`, {
        row_index: rowIndex,
        category: category
      });
      setProgress(res.data.progress);
      setError(null);
    } catch (err) {
      setError('Failed to map row: ' + err.message);
    }
  };

  if (loading) {
    return <div className="app loading">Loading...</div>;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Budget Planner</h1>
        <p>Map your expenses to budget categories</p>
      </header>

      {error && <div className="error-message">{error}</div>}

      <main className="app-main">
        <div className="sidebar">
          <FileUpload onFileUpload={handleFileUpload} />
          {progress && <Stats progress={progress} />}
        </div>

        <div className="content">
          {progress && progress.total_rows > 0 ? (
            <MappingInterface
              progress={progress}
              categories={categories}
              onMapRow={handleMapRow}
            />
          ) : (
            <div className="placeholder">
              <p>Upload a file to get started</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
