import React, { useState, useMemo } from 'react';
import axios from 'axios';
import './MappingInterface.css';
import ReviewScreen from './ReviewScreen';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function MappingInterface({ progress, categories, onMapRow, onAddCategory, onConfirmAddCategory, onSuggestCategory }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategoryInput, setNewCategoryInput] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestion, setSuggestion] = useState(null);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [showReviewScreen, setShowReviewScreen] = useState(false);
  const [bulkMappings, setBulkMappings] = useState(null);
  const [bulkMappingError, setBulkMappingError] = useState(null);
  const [processingProgress, setProcessingProgress] = useState(null);

  const rows = useMemo(() => {
    if (!progress.rows) return [];
    return Object.entries(progress.rows).map(([idx, data]) => ({
      index: parseInt(idx),
      ...data
    })).sort((a, b) => a.index - b.index);
  }, [progress.rows]);

  const unmappedRows = rows.filter(row => !row.mapped);
  const currentRow = unmappedRows[currentIndex];

  const handleMapCategory = (category) => {
    if (currentRow) {
      onMapRow(currentRow.index, category);
      if (currentIndex < unmappedRows.length - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < unmappedRows.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleSubmitNewCategory = async () => {
    if (!newCategoryInput.trim()) {
      return;
    }

    setIsProcessing(true);
    const result = await onAddCategory(newCategoryInput);

    if (result.needsConfirmation) {
      setValidationResult(result.validation);
    } else if (result.success) {
      setNewCategoryInput('');
      setShowAddCategory(false);
      setValidationResult(null);
    }

    setIsProcessing(false);
  };

  const handleConfirmCorrections = async () => {
    if (!validationResult) return;

    setIsProcessing(true);
    const result = await onConfirmAddCategory(validationResult.corrected);

    if (result.success) {
      setNewCategoryInput('');
      setShowAddCategory(false);
      setValidationResult(null);
    }

    setIsProcessing(false);
  };

  const handleCancelAddCategory = () => {
    setShowAddCategory(false);
    setNewCategoryInput('');
    setValidationResult(null);
  };

  const handleRequestSuggestion = async () => {
    if (!currentRow) return;

    setIsSuggesting(true);
    const result = await onSuggestCategory(currentRow.index, currentRow.data);

    if (result.success) {
      setSuggestion(result.suggestion);
    }

    setIsSuggesting(false);
  };

  const handleAcceptSuggestion = () => {
    if (suggestion && currentRow) {
      handleMapCategory(suggestion);
      setSuggestion(null);
    }
  };

  const handleRejectSuggestion = () => {
    setSuggestion(null);
  };

  const handleBulkMap = async () => {
    try {
      setIsProcessing(true);
      setBulkMappingError(null);
      setProcessingProgress({ current: 0, total: unmappedRows.length });

      const res = await axios.post(`${API_BASE_URL}/bulk-map`, {}, {
        timeout: 900000 // 15 minute timeout for bulk processing
      });

      if (res.data.success) {
        setBulkMappings(res.data.mappings);
        setProcessingProgress({
          current: res.data.progress?.total || unmappedRows.length,
          total: unmappedRows.length
        });
        setShowReviewScreen(true);
      } else {
        setBulkMappingError(res.data.error || 'Failed to generate bulk mappings');
      }
    } catch (err) {
      console.error('Bulk map error:', err);
      setBulkMappingError('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingProgress(null), 1000); // Keep showing 100% for a moment
    }
  };

  const handleReviewClose = () => {
    setShowReviewScreen(false);
    setBulkMappings(null);
  };

  const handleReviewConfirm = (mappings) => {
    // Reload the page to update progress
    window.location.reload();
  };

  const progress_percentage = rows.length > 0
    ? Math.round((rows.filter(r => r.mapped).length / rows.length) * 100)
    : 0;

  // Show progress modal while processing
  if (processingProgress) {
    const percentComplete = processingProgress.total > 0
      ? Math.round((processingProgress.current / processingProgress.total) * 100)
      : 0;

    return (
      <div className="mapping-interface">
        <div className="processing-modal">
          <div className="processing-content">
            <h2>🤖 AI Processing...</h2>
            <p>Generating suggestions for {processingProgress.total} items</p>
            <div className="progress-bar-large">
              <div className="progress-fill-large" style={{ width: `${percentComplete}%` }}></div>
            </div>
            <p className="progress-text">
              {processingProgress.current} / {processingProgress.total} items ({percentComplete}%)
            </p>
            <p className="processing-note">This may take a minute depending on the number of items...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show review screen if active
  if (showReviewScreen && bulkMappings) {
    return (
      <ReviewScreen
        mappings={bulkMappings}
        categories={categories}
        onConfirm={handleReviewConfirm}
        onCancel={handleReviewClose}
      />
    );
  }

  if (!currentRow) {
    return (
      <div className="mapping-interface complete">
        <div className="complete-message">
          <h2>✓ All rows mapped!</h2>
          <p>You've successfully categorized all {rows.length} transactions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mapping-interface">
      <div className="file-info">
        <div className="file-name">
          <span className="file-icon">📄</span>
          <span className="file-text">{progress.file_name || 'Unknown File'}</span>
        </div>
        <div className="file-stats">
          {progress.total_rows} total rows • {rows.filter(r => r.mapped).length} mapped • {unmappedRows.length} remaining
        </div>
      </div>

      <div className="progress-bar-container">
        <div className="progress-label">
          Progress: {currentIndex + 1} of {unmappedRows.length}
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress_percentage}%` }}
          ></div>
        </div>
      </div>

      <div className="row-card">
        <div className="row-content">
          <h3>Row #{currentRow.index + 1}</h3>
          <div className="row-details">
            {Object.entries(currentRow.data).map(([key, value]) => (
              <div key={key} className="row-field">
                <span className="field-label">{key}:</span>
                <span className="field-value">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="category-selection">
          <div className="category-header">
            <p>Select a budget category:</p>
            <div className="category-buttons">
              <button
                className="suggest-button"
                onClick={handleRequestSuggestion}
                disabled={isSuggesting}
                title="Get AI-powered category suggestion"
              >
                {isSuggesting ? '🤖 Suggesting...' : '💡 Suggest'}
              </button>
              <button
                className="add-category-button"
                onClick={() => setShowAddCategory(true)}
                title="Add a new custom category"
              >
                + Add Category
              </button>
              <button
                className="bulk-map-button"
                onClick={handleBulkMap}
                disabled={isProcessing}
                title="Use AI to suggest categories for all remaining items"
              >
                {isProcessing ? '⚙️ Processing...' : '🚀 AI Map All'}
              </button>
            </div>
          </div>

          {bulkMappingError && (
            <div className="mapping-error">
              {bulkMappingError}
            </div>
          )}

          {suggestion && (
            <div className="suggestion-panel">
              <div className="suggestion-content">
                <p className="suggestion-label">AI Suggestion:</p>
                <p className="suggestion-value">{suggestion}</p>
              </div>
              <div className="suggestion-buttons">
                <button
                  className="yes-button"
                  onClick={handleAcceptSuggestion}
                >
                  ✓ Yes
                </button>
                <button
                  className="no-button"
                  onClick={handleRejectSuggestion}
                >
                  ✗ No
                </button>
              </div>
            </div>
          )}

          <div className="category-grid">
            {categories.map(category => (
              <button
                key={category}
                className="category-button"
                onClick={() => handleMapCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          {showAddCategory && (
            <div className="add-category-modal">
              <div className="modal-content">
                <h3>Add New Category</h3>

                {!validationResult ? (
                  <>
                    <input
                      type="text"
                      placeholder="Enter category name"
                      value={newCategoryInput}
                      onChange={(e) => setNewCategoryInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSubmitNewCategory();
                        }
                      }}
                      className="category-input"
                      disabled={isProcessing}
                    />
                    <div className="modal-buttons">
                      <button
                        onClick={handleSubmitNewCategory}
                        className="confirm-button"
                        disabled={!newCategoryInput.trim() || isProcessing}
                      >
                        {isProcessing ? 'Processing...' : 'Add'}
                      </button>
                      <button
                        onClick={handleCancelAddCategory}
                        className="cancel-button"
                        disabled={isProcessing}
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="validation-message">
                      <p><strong>Original:</strong> {validationResult.original}</p>
                      <p><strong>Suggested:</strong> {validationResult.corrected}</p>
                      {validationResult.corrections.length > 0 && (
                        <div className="corrections-list">
                          <p><strong>Corrections made:</strong></p>
                          <ul>
                            {validationResult.corrections.map((correction, idx) => (
                              <li key={idx}>{correction}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    <div className="modal-buttons">
                      <button
                        onClick={handleConfirmCorrections}
                        className="confirm-button"
                        disabled={isProcessing}
                      >
                        {isProcessing ? 'Adding...' : 'Confirm & Add'}
                      </button>
                      <button
                        onClick={handleCancelAddCategory}
                        className="cancel-button"
                        disabled={isProcessing}
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="navigation">
        <button
          className="nav-button prev"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        >
          ← Previous
        </button>
        <span className="nav-info">
          Showing unmapped row {currentIndex + 1} of {unmappedRows.length}
        </span>
        <button
          className="nav-button next"
          onClick={handleNext}
          disabled={currentIndex === unmappedRows.length - 1}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

export default MappingInterface;
