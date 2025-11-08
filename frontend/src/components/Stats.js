import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './Stats.css';

const API_BASE_URL = 'http://localhost:5000/api';

function Stats({ progress }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/stats`);
        setStats(res.data);
      } catch (err) {
        console.error('Failed to load stats:', err);
      }
    };

    loadStats();
    const interval = setInterval(loadStats, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (!stats) {
    return <div className="stats loading">Loading stats...</div>;
  }

  const categories = Object.entries(stats.category_breakdown || {})
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="stats">
      <h2>Progress</h2>

      <div className="stat-item">
        <span className="stat-label">File:</span>
        <span className="stat-value">{stats.file_name || 'No file'}</span>
      </div>

      <div className="stat-item highlight">
        <span className="stat-label">Mapped:</span>
        <span className="stat-value">{stats.mapped_rows} / {stats.total_rows}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Remaining:</span>
        <span className="stat-value warning">{stats.remaining_rows}</span>
      </div>

      {categories.length > 0 && (
        <div className="breakdown">
          <h3>Category Breakdown</h3>
          <div className="breakdown-list">
            {categories.map(([category, count]) => (
              <div key={category} className="breakdown-item">
                <span className="breakdown-label">{category}</span>
                <span className="breakdown-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats.last_updated && (
        <div className="last-updated">
          Last updated: {new Date(stats.last_updated).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

export default Stats;
