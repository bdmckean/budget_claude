import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import FileUpload from './components/FileUpload';
import MappingInterface from './components/MappingInterface';
import Stats from './components/Stats';
import Analytics from './components/Analytics';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function App() {
  const [progress, setProgress] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [infoMessage, setInfoMessage] = useState(null);
  const [currentPage, setCurrentPage] = useState('mapping'); // 'mapping' or 'analytics'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async (retries = 3, delay = 1000) => {
    try {
      setLoading(true);
      const [categoriesRes, progressRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/categories`, { timeout: 5000 }),
        axios.get(`${API_BASE_URL}/progress`, { timeout: 5000 })
      ]);
      setCategories(categoriesRes.data.categories);
      setProgress(progressRes.data);
      setError(null);
      setLoading(false);
    } catch (err) {
      const isNetworkError = err.code === 'ECONNABORTED' || err.message === 'Network Error';
      if (retries > 0 && isNetworkError) {
        // Retry after delay if network error
        setTimeout(() => {
          loadData(retries - 1, delay * 2);
        }, delay);
      } else {
        setError('Failed to load data: ' + err.message);
        setLoading(false);
      }
    }
  };

  const handleReset = async () => {
    try {
      if (!progress || !progress.file_name) {
        setError('No file loaded to reset');
        return;
      }
      const res = await axios.post(`${API_BASE_URL}/reset-file`, {
        file_name: progress.file_name
      });
      setProgress(res.data.progress);
      setError(null);
    } catch (err) {
      console.error('Reset error:', err);
      let errorMsg = 'Failed to reset file: ' + err.message;
      if (err.response) {
        console.error('Response data:', err.response.data);
        errorMsg = 'Reset error: ' + (err.response.data.error || JSON.stringify(err.response.data));
      }
      setError(errorMsg);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API_BASE_URL}/upload`, formData);
      setProgress(res.data.progress);
      setError(null);

      // Display info message if provided
      if (res.data.message) {
        setInfoMessage(res.data.message);
        // Auto-clear after 5 seconds
        setTimeout(() => setInfoMessage(null), 5000);
      }
    } catch (err) {
      console.error('Upload error:', err);
      let errorMsg = 'Failed to upload file: ' + err.message;
      if (err.response) {
        console.error('Response data:', err.response.data);
        errorMsg = 'Upload error: ' + JSON.stringify(err.response.data);
      }
      setError(errorMsg);
      setInfoMessage(null);
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

  const handleAddCategory = async (categoryName) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/add-category`, {
        category_name: categoryName
      });

      // If there are corrections, return them for user confirmation
      if (res.data.validation && res.data.validation.has_corrections) {
        return {
          success: false,
          needsConfirmation: true,
          validation: res.data.validation
        };
      }

      // If no corrections needed, add directly
      const confirmRes = await axios.post(`${API_BASE_URL}/confirm-add-category`, {
        category: res.data.validation.corrected
      });

      // Update categories list
      setCategories(confirmRes.data.categories);
      setError(null);
      return {
        success: true,
        category: confirmRes.data.categories[confirmRes.data.categories.length - 1]
      };
    } catch (err) {
      console.error('Add category error:', err);
      let errorMsg = 'Failed to add category: ' + err.message;
      if (err.response) {
        console.error('Response data:', err.response.data);
        errorMsg = 'Add category error: ' + (err.response.data.error || JSON.stringify(err.response.data));
      }
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const handleConfirmAddCategory = async (correctedCategory) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/confirm-add-category`, {
        category: correctedCategory
      });

      // Update categories list
      setCategories(res.data.categories);
      setError(null);
      return {
        success: true,
        category: correctedCategory,
        message: res.data.message
      };
    } catch (err) {
      console.error('Confirm add category error:', err);
      let errorMsg = 'Failed to add category: ' + err.message;
      if (err.response) {
        console.error('Response data:', err.response.data);
        errorMsg = 'Add category error: ' + (err.response.data.error || JSON.stringify(err.response.data));
      }
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const handleSuggestCategory = async (rowIndex, transactionData) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/suggest-category`, {
        row_index: rowIndex,
        transaction_data: transactionData
      });

      if (res.data.success) {
        setError(null);
        return {
          success: true,
          suggestion: res.data.suggestion
        };
      } else {
        setError('Suggestion failed: ' + res.data.error);
        return {
          success: false,
          error: res.data.error
        };
      }
    } catch (err) {
      setError('Failed to get suggestion: ' + err.message);
      return { success: false, error: err.message };
    }
  };

  if (loading) {
    return <div className="app loading">Loading...</div>;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div>
            <h1>Budget Planner Claude</h1>
            <p>Map your expenses to budget categories</p>
          </div>
          <nav className="page-nav">
            <button
              className={`nav-button ${currentPage === 'mapping' ? 'active' : ''}`}
              onClick={() => setCurrentPage('mapping')}
            >
              📊 Mapping
            </button>
            <button
              className={`nav-button ${currentPage === 'analytics' ? 'active' : ''}`}
              onClick={() => setCurrentPage('analytics')}
            >
              📈 Analytics
            </button>
          </nav>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}
      {infoMessage && <div className="info-message">{infoMessage}</div>}

      <main className="app-main">
        {currentPage === 'mapping' ? (
          <>
            <div className="sidebar">
              <FileUpload
                onFileUpload={handleFileUpload}
                onReset={handleReset}
                hasFile={progress && progress.total_rows > 0}
              />
              {progress && <Stats progress={progress} />}
            </div>

            <div className="content">
              {progress && progress.total_rows > 0 ? (
                <MappingInterface
                  progress={progress}
                  categories={categories}
                  onMapRow={handleMapRow}
                  onAddCategory={handleAddCategory}
                  onConfirmAddCategory={handleConfirmAddCategory}
                  onSuggestCategory={handleSuggestCategory}
                />
              ) : (
                <div className="placeholder">
                  <p>Upload a file to get started</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="analytics-page">
            <Analytics />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
