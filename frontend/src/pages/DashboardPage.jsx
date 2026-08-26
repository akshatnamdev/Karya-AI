import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import dashboardService from '../services/dashboardService';
import { Loader2, ArrowRight } from 'lucide-react';
import '../styles/Dashboard.css';

function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await dashboardService.getDashboardData();
        setData(response);
        setError('');
      } catch (err) {
        console.error('Dashboard error:', err);
        setError(err.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="loading-container">
          <Loader2 size={20} className="spin" />
        </div>
      </Layout>
    );
  }

  const alerts = data?.alerts || [];
  const summary = data?.summary || {};

  return (
    <Layout>
      <header className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-subtitle">{data?.business?.name || 'Welcome back'}</p>
      </header>

      {error && (
        <div style={{ color: '#991b1b', fontSize: 13, marginBottom: 16 }}>{error}</div>
      )}

      <div className="metrics-row">
        <div className="metric-item">
          <span className="metric-label">Total Revenue</span>
          <span className="metric-value">{summary.total_revenue || '₹0.00'}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Outstanding</span>
          <span className="metric-value">{summary.total_outstanding || '₹0.00'}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Customers</span>
          <span className="metric-value">{summary.total_customers ?? 0}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Stock Value</span>
          <span className="metric-value">{summary.total_stock_value || '₹0.00'}</span>
        </div>
      </div>

      {/* Real API alerts only — no hardcoded Raj Traders */}
      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Requires Attention</h2>
        </div>
        {alerts.length === 0 ? (
          <div className="attention-list">
            <div className="attention-item">
              <span className="status-dot green"></span>
              No alerts right now
            </div>
          </div>
        ) : (
          <div className="attention-list">
            {alerts.map((alert, index) => {
              const dotClass =
                alert.type === 'danger' ? 'red' :
                alert.type === 'warning' ? 'amber' : 'green';
              const path =
                alert.type === 'danger' ? '/invoices' :
                alert.type === 'warning' ? '/products' : '/orders';
              return (
                <div
                  key={index}
                  className="attention-item"
                  onClick={() => navigate(path)}
                >
                  <span className={`status-dot ${dotClass}`}></span>
                  {alert.message}
                </div>
              );
            })}
          </div>
        )}
      </section>

      <div className="two-column-grid">
        <section className="dashboard-section" style={{ marginBottom: 0 }}>
          <div className="section-header">
            <h2 className="section-title">Business</h2>
            <Link to="/customers" className="section-link">Customers →</Link>
          </div>
          <table className="compact-table">
            <tbody>
              <tr>
                <td className="text-muted">Type</td>
                <td>{data?.business?.type || '—'}</td>
              </tr>
              <tr>
                <td className="text-muted">City</td>
                <td>{data?.business?.city || '—'}</td>
              </tr>
              <tr>
                <td className="text-muted">Orders</td>
                <td>{summary.total_orders ?? 0}</td>
              </tr>
              <tr>
                <td className="text-muted">Products</td>
                <td>{summary.total_products ?? 0}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="dashboard-section" style={{ marginBottom: 0 }}>
          <div className="section-header">
            <h2 className="section-title">Quick links</h2>
          </div>
          <table className="compact-table">
            <tbody>
              <tr style={{ cursor: 'pointer' }} onClick={() => navigate('/orders')}>
                <td>Orders</td>
                <td className="text-muted">View all →</td>
              </tr>
              <tr style={{ cursor: 'pointer' }} onClick={() => navigate('/invoices')}>
                <td>Invoices</td>
                <td className="text-muted">View all →</td>
              </tr>
              <tr style={{ cursor: 'pointer' }} onClick={() => navigate('/products')}>
                <td>Inventory</td>
                <td className="text-muted">View all →</td>
              </tr>
              <tr style={{ cursor: 'pointer' }} onClick={() => navigate('/assistant')}>
                <td>Assistant</td>
                <td className="text-muted">Ask Karya →</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <section className="dashboard-section">
        <div className="ask-karya">
          <div className="ask-karya-left">
            <h3 className="ask-title">Ask Karya</h3>
            <p className="ask-desc">Need a quick answer about your business?</p>
            <div className="ask-examples">
              <span className="ask-example">What invoices are overdue?</span>
              <span className="ask-example">Which products need reordering?</span>
              <span className="ask-example">How much did we sell this month?</span>
            </div>
          </div>
          <Link to="/assistant" className="btn-secondary">
            Open Assistant <ArrowRight size={14} />
          </Link>
        </div>
      </section>
    </Layout>
  );
}

export default DashboardPage;