import React, { useState, useMemo } from 'react';
import './MappingInterface.css';

function MappingInterface({ progress, categories, onMapRow }) {
  const [currentIndex, setCurrentIndex] = useState(0);

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

  const progress_percentage = rows.length > 0
    ? Math.round((rows.filter(r => r.mapped).length / rows.length) * 100)
    : 0;

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
          <p>Select a budget category:</p>
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
