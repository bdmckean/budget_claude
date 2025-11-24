import React, { useState } from 'react';
import axios from 'axios';
import './ReviewScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function ReviewScreen({ mappings, categories, onConfirm, onCancel }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [mappingEdits, setMappingEdits] = useState(mappings);
  const [filter, setFilter] = useState('all'); // 'all', 'confirmed', 'unconfirmed'
  const [error, setError] = useState(null);

  // Filter mappings based on current filter
  const mappingEntries = Object.entries(mappingEdits);
  const filteredEntries = mappingEntries.filter(([_, data]) => {
    if (filter === 'confirmed') return data.confirmed;
    if (filter === 'unconfirmed') return !data.confirmed;
    return true;
  });

  if (filteredEntries.length === 0) {
    return (
      <div className="review-screen">
        <div className="review-empty">
          <p>No items to review</p>
          <button className="action-button" onClick={onCancel}>Back</button>
        </div>
      </div>
    );
  }

  const [currentRowIndex, currentData] = filteredEntries[currentIndex] || [];
  const itemData = currentData?.data || {};
  const currentSuggestion = currentData?.suggestion;
  const isConfirmed = currentData?.confirmed;

  const handleSuggestionChange = (e) => {
    const newCategory = e.target.value;
    setMappingEdits(prev => ({
      ...prev,
      [currentRowIndex]: {
        ...prev[currentRowIndex],
        suggestion: newCategory
      }
    }));
  };

  const handleConfirm = () => {
    if (!currentSuggestion) {
      setError('Please select a category');
      return;
    }
    setMappingEdits(prev => ({
      ...prev,
      [currentRowIndex]: {
        ...prev[currentRowIndex],
        confirmed: true
      }
    }));
    // Move to next unconfirmed
    const nextIndex = filteredEntries.findIndex(([_, data], idx) =>
      idx > currentIndex && !data.confirmed
    );
    if (nextIndex >= 0) {
      setCurrentIndex(nextIndex);
    } else {
      setCurrentIndex(currentIndex + 1);
    }
    setError(null);
  };

  const handleSkip = () => {
    setCurrentIndex(currentIndex + 1);
    setError(null);
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setError(null);
    }
  };

  const handleNext = () => {
    if (currentIndex < filteredEntries.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setError(null);
    }
  };

  const handleUnconfirm = () => {
    // Allow user to unconfirm a previously confirmed entry to edit it
    setMappingEdits(prev => ({
      ...prev,
      [currentRowIndex]: {
        ...prev[currentRowIndex],
        confirmed: false
      }
    }));
    setError(null);
  };

  const handleConfirmAll = async () => {
    try {
      // Confirm all mappings with the API
      const confirmPromises = [];
      Object.entries(mappingEdits).forEach(([rowIndex, data]) => {
        if (data.suggestion) {
          confirmPromises.push(
            axios.post(`${API_BASE_URL}/map-row`, {
              row_index: parseInt(rowIndex),
              category: data.suggestion
            })
          );
        }
      });

      if (confirmPromises.length > 0) {
        await Promise.all(confirmPromises);
      }

      // Call the parent callback
      onConfirm(mappingEdits);
    } catch (err) {
      console.error('Error confirming mappings:', err);
      setError('Failed to save mappings: ' + err.message);
    }
  };

  const confirmedCount = Object.values(mappingEdits).filter(d => d.confirmed).length;
  const totalCount = Object.values(mappingEdits).length;

  return (
    <div className="review-screen">
      <div className="review-header">
        <h2>Review AI Mappings</h2>
        <div className="review-stats">
          <span className="stat">
            Item {currentIndex + 1} of {filteredEntries.length}
          </span>
          <span className="stat">
            Confirmed: {confirmedCount}/{totalCount}
          </span>
        </div>
      </div>

      {error && <div className="review-error">{error}</div>}

      <div className="review-filters">
        <label>Filter:</label>
        <select value={filter} onChange={(e) => {
          setFilter(e.target.value);
          setCurrentIndex(0);
        }}>
          <option value="all">All ({mappingEntries.length})</option>
          <option value="unconfirmed">
            Unconfirmed ({mappingEntries.filter(([_, d]) => !d.confirmed).length})
          </option>
          <option value="confirmed">
            Confirmed ({mappingEntries.filter(([_, d]) => d.confirmed).length})
          </option>
        </select>
      </div>

      <div className="review-item">
        <div className="transaction-details">
          <div className="detail-row">
            <label>Date:</label>
            <span>{itemData['Transaction Date'] || itemData['Date'] || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <label>Amount:</label>
            <span className="amount">{itemData['Amount'] || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <label>Description:</label>
            <span className="description">{itemData['Description'] || 'N/A'}</span>
          </div>
          {itemData['Category'] && (
            <div className="detail-row">
              <label>Original Category:</label>
              <span className="original-category">{itemData['Category']}</span>
            </div>
          )}
        </div>

        <div className="suggestion-section">
          <label htmlFor="category-select">AI Suggestion:</label>
          <select
            id="category-select"
            value={currentSuggestion || ''}
            onChange={handleSuggestionChange}
            className={`category-select ${isConfirmed ? 'confirmed' : ''}`}
          >
            <option value="">-- Select Category --</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {isConfirmed && <div className="confirmed-badge">✓ Confirmed</div>}
      </div>

      <div className="review-controls">
        <button
          className="control-button secondary"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        >
          ← Previous
        </button>

        {!isConfirmed ? (
          <>
            <button
              className="control-button danger"
              onClick={handleSkip}
            >
              Skip
            </button>
            <button
              className="control-button primary"
              onClick={handleConfirm}
              disabled={!currentSuggestion}
            >
              Confirm
            </button>
          </>
        ) : (
          <>
            <button
              className="control-button warning"
              onClick={handleUnconfirm}
              title="Unconfirm to edit this entry"
            >
              ✏️ Edit
            </button>
            <button className="control-button success" disabled>
              Confirmed ✓
            </button>
          </>
        )}

        <button
          className="control-button secondary"
          onClick={handleNext}
          disabled={currentIndex >= filteredEntries.length - 1}
        >
          Next →
        </button>
      </div>

      <div className="review-actions">
        <button className="action-button secondary" onClick={onCancel}>
          Cancel
        </button>
        <button
          className="action-button primary"
          onClick={handleConfirmAll}
          disabled={confirmedCount === 0}
        >
          Save {confirmedCount > 0 ? `(${confirmedCount} items)` : ''}
        </button>
      </div>
    </div>
  );
}

export default ReviewScreen;
