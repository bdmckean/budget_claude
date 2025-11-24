import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Analytics.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE_URL}/analytics`);
      if (res.data.success) {
        setAnalytics(res.data);
        setError(null);
      } else {
        setError(res.data.error || 'Failed to load analytics');
      }
    } catch (err) {
      console.error('Analytics error:', err);
      setError('Failed to load analytics: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="analytics loading">Loading analytics...</div>;
  }

  if (error) {
    return <div className="analytics error">Error: {error}</div>;
  }

  if (!analytics || !analytics.spending_by_month || Object.keys(analytics.spending_by_month).length === 0) {
    return <div className="analytics empty">No spending data available. Map some transactions first!</div>;
  }

  const spending_by_month = analytics.spending_by_month;
  const category_totals = analytics.category_totals;
  const months = analytics.months;

  // Get all unique categories across all months
  const all_categories = Array.from(
    new Set(Object.values(spending_by_month).flatMap(month => Object.keys(month)))
  ).sort();

  return (
    <div className="analytics-container">
      <h2>Spending Analytics</h2>

      {/* Summary by Category */}
      <section className="analytics-section">
        <h3>Total Spending by Category</h3>
        <div className="category-summary">
          {Object.entries(category_totals)
            .sort(([, a], [, b]) => b - a)
            .map(([category, total]) => (
              <div key={category} className="category-item">
                <div className="category-name">{category}</div>
                <div className="category-amount">${total.toFixed(2)}</div>
              </div>
            ))}
        </div>
      </section>

      {/* Month by Month Table */}
      <section className="analytics-section">
        <h3>Monthly Breakdown</h3>
        <div className="table-wrapper">
          <table className="spending-table">
            <thead>
              <tr>
                <th className="category-col">Category</th>
                {months.map(month => (
                  <th key={month} className="month-col">{month}</th>
                ))}
                <th className="total-col">Total</th>
              </tr>
            </thead>
            <tbody>
              {all_categories.map(category => (
                <tr key={category}>
                  <td className="category-cell">{category}</td>
                  {months.map(month => (
                    <td key={`${month}-${category}`} className="amount-cell">
                      {spending_by_month[month][category]
                        ? `$${spending_by_month[month][category].toFixed(2)}`
                        : '-'}
                    </td>
                  ))}
                  <td className="total-cell">
                    ${(category_totals[category] || 0).toFixed(2)}
                  </td>
                </tr>
              ))}
              {/* Monthly totals row */}
              <tr className="totals-row">
                <td className="category-cell">Monthly Total</td>
                {months.map(month => {
                  const monthTotal = Object.values(spending_by_month[month]).reduce((a, b) => a + b, 0);
                  return (
                    <td key={`total-${month}`} className="amount-cell">
                      ${monthTotal.toFixed(2)}
                    </td>
                  );
                })}
                <td className="total-cell">
                  ${Object.values(category_totals).reduce((a, b) => a + b, 0).toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Refresh button */}
      <button className="refresh-button" onClick={loadAnalytics}>
        <span className="icon">🔄</span>
        Refresh Analytics
      </button>
    </div>
  );
}

export default Analytics;
