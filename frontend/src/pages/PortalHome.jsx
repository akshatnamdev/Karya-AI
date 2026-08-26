import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import orderService from '../services/orderService';
import invoiceService from '../services/invoiceService';
import productService from '../services/productService';
import { Loader2 } from 'lucide-react';
import '../styles/Dashboard.css';

function PortalHome() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [o, inv, p] = await Promise.all([
          orderService.getAll().catch(() => []),
          invoiceService.getAll().catch(() => []),
          productService.getAll().catch(() => []),
        ]);
        setOrders(Array.isArray(o) ? o : []);
        setInvoices(Array.isArray(inv) ? inv : []);
        setProducts(Array.isArray(p) ? p : []);
      } catch (e) {
        setError('Could not load portal data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  const outstanding = invoices.reduce((s, i) => s + (Number(i.balance) || 0), 0);

  if (loading) {
    return (
      <Layout>
        <div className="loading-container">
          <Loader2 size={20} className="spin" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <header className="page-header">
        <h1 className="page-title">My portal</h1>
        <p className="page-subtitle">Welcome, {user?.name}</p>
      </header>

      {error && (
        <div style={{ color: '#991b1b', fontSize: 13, marginBottom: 16 }}>{error}</div>
      )}

      <div className="metrics-row">
        <div className="metric-item">
          <span className="metric-label">My orders</span>
          <span className="metric-value">{orders.length}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">My invoices</span>
          <span className="metric-value">{invoices.length}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Amount due</span>
          <span className="metric-value">{formatMoney(outstanding)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Products available</span>
          <span className="metric-value">{products.length}</span>
        </div>
      </div>

      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">What you can do</h2>
        </div>
        <div className="attention-list">
          <Link to="/products" className="attention-item" style={{ textDecoration: 'none', color: 'inherit' }}>
            Browse catalog and see available products
          </Link>
          <Link to="/orders" className="attention-item" style={{ textDecoration: 'none', color: 'inherit' }}>
            View my order history
          </Link>
          <Link to="/invoices" className="attention-item" style={{ textDecoration: 'none', color: 'inherit' }}>
            View invoices and balances
          </Link>
          <Link to="/assistant" className="attention-item" style={{ textDecoration: 'none', color: 'inherit' }}>
            Ask Assistant about my account
          </Link>
        </div>
      </section>

      <section className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Recent orders</h2>
          <Link to="/orders" className="section-link">View all →</Link>
        </div>
        {orders.length === 0 ? (
          <p className="text-muted">No orders yet. Browse the catalog to get started.</p>
        ) : (
          <table className="compact-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 5).map((o) => (
                <tr key={o.id}>
                  <td className="text-mono">{o.order_number}</td>
                  <td>{formatMoney(o.total)}</td>
                  <td>{o.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </Layout>
  );
}

export default PortalHome;