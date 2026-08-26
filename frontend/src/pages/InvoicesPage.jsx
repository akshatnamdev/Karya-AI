import { useState, useEffect, useMemo } from 'react';
import Layout from '../components/Layout';
import invoiceService from '../services/invoiceService';
import { Loader2 } from 'lucide-react';
import '../styles/DataPage.css';

function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [overdue, setOverdue] = useState(null);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [all, overdueData] = await Promise.all([
        invoiceService.getAll().catch(() => []),
        invoiceService.getOverdue().catch(() => ({ count: 0, invoices: [] })),
      ]);
      setInvoices(Array.isArray(all) ? all : []);
      setOverdue(overdueData || null);
    } catch (err) {
      console.error(err);
      setError('Could not load invoices right now.');
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (invoice) => {
    setSelected(invoice);
    setDetailLoading(true);
    setDetail(null);
    try {
      const data = await invoiceService.getById(invoice.id);
      setDetail(data);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const filtered = useMemo(() => {
    let list = invoices;

    if (filter !== 'all') {
      list = list.filter((inv) => inv.status === filter);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (inv) =>
          inv.invoice_number?.toLowerCase().includes(q) ||
          inv.customer?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [invoices, search, filter]);

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  const statusDot = (status) => {
    if (status === 'paid') return 'green';
    if (status === 'overdue') return 'red';
    if (status === 'partially_paid' || status === 'sent') return 'amber';
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
      <header className="page-header">
        <h1 className="page-title">Invoices</h1>
        <p className="page-subtitle">
          {invoices.length} invoices
          {overdue?.count > 0
            ? ` · ${overdue.count} overdue (${formatMoney(overdue.total_overdue_amount)})`
            : ''}
        </p>
      </header>

      {error && (
        <div style={{ color: '#991b1b', marginBottom: 16, fontSize: 13 }}>{error}</div>
      )}

      {overdue?.invoices?.length > 0 && filter === 'all' && (
        <div
          style={{
            border: '1px solid #fecaca',
            background: '#fef2f2',
            borderRadius: 6,
            padding: '12px 16px',
            marginBottom: 20,
            fontSize: 13,
            color: '#991b1b',
          }}
        >
          <strong style={{ fontWeight: 600 }}>Overdue</strong>
          {' — '}
          {overdue.invoices.map((inv, i) => (
            <span key={i}>
              {i > 0 ? ' · ' : ''}
              {inv.customer}: {formatMoney(inv.amount_pending)} ({inv.days_overdue}d)
            </span>
          ))}
        </div>
      )}

      <div className="page-toolbar">
        <input
          className="search-input"
          placeholder="Search invoice or customer..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          <button className={`filter-tab ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All</button>
          <button className={`filter-tab ${filter === 'overdue' ? 'active' : ''}`} onClick={() => setFilter('overdue')}>Overdue</button>
          <button className={`filter-tab ${filter === 'partially_paid' ? 'active' : ''}`} onClick={() => setFilter('partially_paid')}>Partial</button>
          <button className={`filter-tab ${filter === 'paid' ? 'active' : ''}`} onClick={() => setFilter('paid')}>Paid</button>
        </div>
      </div>

      <div className="detail-layout">
        <div className="data-table-wrap">
          {filtered.length === 0 ? (
            <div className="empty-state-box">No invoices found</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Customer</th>
                  <th className="right">Total</th>
                  <th className="right">Balance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inv) => (
                  <tr
                    key={inv.id}
                    className={selected?.id === inv.id ? 'selected' : ''}
                    onClick={() => openDetail(inv)}
                  >
                    <td className="cell-mono">{inv.invoice_number}</td>
                    <td className="cell-primary">{inv.customer}</td>
                    <td className="right">{formatMoney(inv.total)}</td>
                    <td className="right cell-primary">{formatMoney(inv.balance)}</td>
                    <td>
                      <span className="status-pill">
                        <span className={`status-dot ${statusDot(inv.status)}`} />
                        {inv.status?.replace('_', ' ')}
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
            <div className="detail-empty">Select an invoice to view details</div>
          ) : detailLoading ? (
            <div className="loading-box" style={{ padding: 40 }}>
              <Loader2 size={18} className="spin" />
            </div>
          ) : (
            <>
              <div className="detail-panel-title">{selected.invoice_number}</div>

              <div className="detail-row">
                <span className="detail-label">Customer</span>
                <span className="detail-value">
                  {detail?.customer?.name || selected.customer}
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
                <span className="detail-value">
                  <span className="status-pill">
                    <span className={`status-dot ${statusDot(selected.status)}`} />
                    {selected.status?.replace('_', ' ')}
                  </span>
                </span>
              </div>

              <div className="detail-section-label">Amounts</div>
              <div className="detail-row">
                <span className="detail-label">Total</span>
                <span className="detail-value">{formatMoney(selected.total)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Paid</span>
                <span className="detail-value">{formatMoney(selected.paid)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Balance</span>
                <span className="detail-value">{formatMoney(selected.balance)}</span>
              </div>

              <div className="detail-section-label">Dates</div>
              <div className="detail-row">
                <span className="detail-label">Invoice date</span>
                <span className="detail-value">
                  {selected.invoice_date?.slice(0, 10) || '—'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Due date</span>
                <span className="detail-value">
                  {selected.due_date?.slice(0, 10) || '—'}
                </span>
              </div>

              {selected.status === 'overdue' && overdue?.invoices && (
                <>
                  <div className="detail-section-label">Suggested reminder</div>
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
                    {overdue.invoices.find(
                      (i) => i.invoice_number === selected.invoice_number
                    )?.suggested_reminder || '—'}
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

export default InvoicesPage;