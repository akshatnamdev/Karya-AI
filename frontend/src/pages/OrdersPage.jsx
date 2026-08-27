import { useState, useEffect, useMemo } from 'react';
import Layout from '../components/Layout';
import orderService from '../services/orderService';
import { Loader2 } from 'lucide-react';
import '../styles/DataPage.css';
import { useAuth } from '../context/AuthContext'; // fix path if needed
import PlaceOrderModal from '../components/PlaceOrderModal';
import { Plus } from 'lucide-react';

function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const { isBusinessOwner, isCustomer } = useAuth();
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const canPlaceOrder = isBusinessOwner || isCustomer;

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const data = await orderService.getAll();
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load orders');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (order) => {
    setSelected(order);
    setDetailLoading(true);
    setDetail(null);
    try {
      const data = await orderService.getById(order.id);
      setDetail(data);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const filtered = useMemo(() => {
    let list = orders;

    if (filter === 'whatsapp') {
      list = list.filter((o) => o.source === 'whatsapp');
    } else if (filter !== 'all') {
      list = list.filter((o) => o.status === filter);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (o) =>
          o.order_number?.toLowerCase().includes(q) ||
          o.customer_name?.toLowerCase().includes(q) ||
          o.whatsapp_message?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [orders, search, filter]);

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  const statusDot = (status) => {
    if (status === 'delivered') return 'green';
    if (status === 'cancelled') return 'red';
    if (status === 'pending' || status === 'processing') return 'amber';
    return 'gray';
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
      <header className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <h1 className="page-title">Orders</h1>
          <p className="page-subtitle">{orders.length} orders total</p>
        </div>
        {canPlaceOrder && (
          <button
            type="button"
            onClick={() => setShowCreateOrder(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: '#111827',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            <Plus size={16} />
            {isBusinessOwner ? 'Create Order' : 'Place Order'}
          </button>
        )}
      </header>

      {error && (
        <div style={{ color: '#991b1b', marginBottom: 16, fontSize: 13 }}>{error}</div>
      )}

      <div className="page-toolbar">
        <input
          className="search-input"
          placeholder="Search order, customer..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          <button className={`filter-tab ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All</button>
          <button className={`filter-tab ${filter === 'whatsapp' ? 'active' : ''}`} onClick={() => setFilter('whatsapp')}>WhatsApp</button>
          <button className={`filter-tab ${filter === 'delivered' ? 'active' : ''}`} onClick={() => setFilter('delivered')}>Delivered</button>
          <button className={`filter-tab ${filter === 'pending' ? 'active' : ''}`} onClick={() => setFilter('pending')}>Pending</button>
        </div>
      </div>

      <div className="detail-layout">
        <div className="data-table-wrap">
          {filtered.length === 0 ? (
            <div className="empty-state-box">No orders found</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Source</th>
                  <th className="right">Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((o) => (
                  <tr
                    key={o.id}
                    className={selected?.id === o.id ? 'selected' : ''}
                    onClick={() => openDetail(o)}
                  >
                    <td className="cell-mono">{o.order_number}</td>
                    <td className="cell-primary">{o.customer_name}</td>
                    <td className="cell-muted">{o.source || '—'}</td>
                    <td className="right cell-primary">{formatMoney(o.total)}</td>
                    <td>
                      <span className="status-pill">
                        <span className={`status-dot ${statusDot(o.status)}`} />
                        {o.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <aside className="detail-panel">
          {!selected ? (
            <div className="detail-empty">Select an order to view details</div>
          ) : detailLoading ? (
            <div className="loading-box" style={{ padding: 40 }}>
              <Loader2 size={18} className="spin" />
            </div>
          ) : (
            <>
              <div className="detail-panel-title">{selected.order_number}</div>

              <div className="detail-row">
                <span className="detail-label">Customer</span>
                <span className="detail-value">
                  {detail?.customer?.name || selected.customer_name}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Phone</span>
                <span className="detail-value">
                  {detail?.customer?.phone || selected.customer_phone || '—'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status</span>
                <span className="detail-value">{selected.status}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Source</span>
                <span className="detail-value">{selected.source || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Total</span>
                <span className="detail-value">{formatMoney(selected.total)}</span>
              </div>

              {(detail?.order?.original_message || selected.whatsapp_message) && (
                <>
                  <div className="detail-section-label">Original message</div>
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
                    {detail?.order?.original_message || selected.whatsapp_message}
                  </div>
                </>
              )}

              <div className="detail-section-label">Items</div>
              {detail?.items?.length > 0 ? (
                detail.items.map((item, i) => (
                  <div className="detail-row" key={i}>
                    <span className="detail-label">
                      {item.product_name}
                      <span className="cell-muted"> × {item.quantity}</span>
                    </span>
                    <span className="detail-value">{formatMoney(item.total)}</span>
                  </div>
                ))
              ) : (
                <div className="detail-empty">No line items</div>
              )}
            </>
          )}
        </aside>
      </div>
            {canPlaceOrder && (
        <PlaceOrderModal
          open={showCreateOrder}
          onClose={() => setShowCreateOrder(false)}
          mode={isBusinessOwner ? 'business' : 'customer'}
          onCreated={() => {
            loadOrders();
          }}
        />
      )}
    </Layout>
  );
}

export default OrdersPage;