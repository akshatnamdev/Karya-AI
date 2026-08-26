import { useState, useEffect, useMemo } from 'react';
import Layout from '../components/Layout';
import customerService from '../services/customerService';
import { Loader2, ArrowLeft } from 'lucide-react';
import '../styles/DataPage.css';

function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const data = await customerService.getAll();
      setCustomers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load customers');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (customer) => {
    setSelected(customer);
    setDetailLoading(true);
    setDetail(null);
    try {
      const data = await customerService.getById(customer.id);
      setDetail(data);
    } catch (err) {
      console.error(err);
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const filtered = useMemo(() => {
    let list = customers;

    if (filter === 'outstanding') {
      list = list.filter((c) => (c.outstanding || 0) > 0);
    } else if (filter === 'clear') {
      list = list.filter((c) => (c.outstanding || 0) === 0);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.name?.toLowerCase().includes(q) ||
          c.phone?.includes(q) ||
          c.city?.toLowerCase().includes(q) ||
          c.type?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [customers, search, filter]);

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  const outstandingStatus = (amount) => {
    if (!amount || amount <= 0) return { dot: 'green', label: 'Clear' };
    if (amount >= 20000) return { dot: 'red', label: 'High' };
    return { dot: 'amber', label: 'Pending' };
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading-box">
          <Loader2 size={20} className="spin" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <header className="page-header">
        <h1 className="page-title">Customers</h1>
        <p className="page-subtitle">{customers.length} accounts in your business</p>
      </header>

      {error && (
        <div style={{ color: '#991b1b', marginBottom: 16, fontSize: 13 }}>{error}</div>
      )}

      <div className="page-toolbar">
        <input
          className="search-input"
          placeholder="Search name, phone, city..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          <button
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-tab ${filter === 'outstanding' ? 'active' : ''}`}
            onClick={() => setFilter('outstanding')}
          >
            Outstanding
          </button>
          <button
            className={`filter-tab ${filter === 'clear' ? 'active' : ''}`}
            onClick={() => setFilter('clear')}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="detail-layout">
        <div className="data-table-wrap">
          {filtered.length === 0 ? (
            <div className="empty-state-box">No customers found</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Phone</th>
                  <th>City</th>
                  <th className="right">Outstanding</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => {
                  const status = outstandingStatus(c.outstanding);
                  return (
                    <tr
                      key={c.id}
                      className={selected?.id === c.id ? 'selected' : ''}
                      onClick={() => openDetail(c)}
                    >
                      <td className="cell-primary">{c.name}</td>
                      <td className="cell-muted">{c.type || '—'}</td>
                      <td className="cell-mono">{c.phone || '—'}</td>
                      <td className="cell-muted">{c.city || '—'}</td>
                      <td className="right cell-primary">{formatMoney(c.outstanding)}</td>
                      <td>
                        <span className="status-pill">
                          <span className={`status-dot ${status.dot}`} />
                          {status.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <aside className="detail-panel">
          {!selected ? (
            <div className="detail-empty">Select a customer to view details</div>
          ) : detailLoading ? (
            <div className="loading-box" style={{ padding: 40 }}>
              <Loader2 size={18} className="spin" />
            </div>
          ) : (
            <>
              <div className="detail-panel-title">{selected.name}</div>

              <div className="detail-row">
                <span className="detail-label">Type</span>
                <span className="detail-value">{selected.type || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Phone</span>
                <span className="detail-value">{selected.phone || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">WhatsApp</span>
                <span className="detail-value">{selected.whatsapp || selected.phone || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">City</span>
                <span className="detail-value">{selected.city || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Credit limit</span>
                <span className="detail-value">{formatMoney(selected.credit_limit)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Outstanding</span>
                <span className="detail-value">{formatMoney(selected.outstanding)}</span>
              </div>

              {selected.notes && (
                <>
                  <div className="detail-section-label">Notes</div>
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
                    {selected.notes}
                  </div>
                </>
              )}

              <div className="detail-section-label">Orders</div>
              {detail?.recent_orders?.length > 0 ? (
                detail.recent_orders.map((o, i) => (
                  <div className="detail-row" key={i}>
                    <span className="detail-label cell-mono">{o.order_number}</span>
                    <span className="detail-value">{formatMoney(o.total)}</span>
                  </div>
                ))
              ) : (
                <div className="detail-empty">No orders yet</div>
              )}

              {detail && (
                <>
                  <div className="detail-section-label">Summary</div>
                  <div className="detail-row">
                    <span className="detail-label">Total orders</span>
                    <span className="detail-value">{detail.orders_count}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Total business</span>
                    <span className="detail-value">{formatMoney(detail.total_business)}</span>
                  </div>
                </>
              )}
            </>
          )}
        </aside>
      </div>
    </Layout>
  );
}

export default CustomersPage;