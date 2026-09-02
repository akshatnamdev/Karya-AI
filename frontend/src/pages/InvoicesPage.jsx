import { useState, useEffect, useMemo } from 'react';
import Layout from '../components/Layout';
import invoiceService from '../services/invoiceService';
import paymentService from '../services/paymentService';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';
import '../styles/DataPage.css';

const btnPrimary = {
  background: '#111827',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
};

const btnSecondary = {
  background: '#fff',
  color: '#374151',
  border: '1px solid #e5e7eb',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 13,
  cursor: 'pointer',
};

function InvoicesPage() {
  const auth = useAuth() || {};
  const { isBusinessOwner, isCustomer } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [overdue, setOverdue] = useState(null);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  // Manual payment
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState('manual');
  const [payNote, setPayNote] = useState('');
  const [payLoading, setPayLoading] = useState(false);
  const [payError, setPayError] = useState('');
  const [paySuccess, setPaySuccess] = useState('');

  // Payment link (scoped per selected invoice)
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkError, setLinkError] = useState('');
  const [linkInfo, setLinkInfo] = useState(null);
  const [linkCopied, setLinkCopied] = useState(false);

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

  const resetSidePanelForms = () => {
    setPayError('');
    setPaySuccess('');
    setPayAmount('');
    setPayNote('');
    setPayMethod('manual');

    setLinkError('');
    setLinkInfo(null);
    setLinkLoading(false);
    setLinkCopied(false);
  };

  const openDetail = async (invoice) => {
    if (!invoice) return;
    setSelected(invoice);
    setDetailLoading(true);
    setDetail(null);
    resetSidePanelForms();

    try {
      const data = await invoiceService.getById(invoice.id);
      setDetail(data);

      // Prefer fresh values from detail API when present
      const inv = data?.invoice;
      if (inv) {
        setSelected((prev) => ({
          ...(prev || {}),
          id: inv.id ?? invoice.id,
          invoice_number: inv.invoice_number ?? invoice.invoice_number,
          status: inv.status ?? invoice.status,
          total: inv.total ?? invoice.total,
          paid: inv.paid ?? invoice.paid,
          balance: inv.balance ?? invoice.balance,
          invoice_date: inv.invoice_date ?? invoice.invoice_date,
          due_date: inv.due_date ?? invoice.due_date,
          customer: data?.customer?.name ?? invoice.customer,
          customer_phone: data?.customer?.phone ?? invoice.customer_phone,
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const syncSelectedFromDetail = (data) => {
    const inv = data?.invoice || {};
    setSelected((prev) => ({
      ...(prev || {}),
      id: inv.id ?? prev?.id,
      invoice_number: inv.invoice_number ?? prev?.invoice_number,
      status: inv.status ?? prev?.status,
      total: inv.total ?? prev?.total,
      paid: inv.paid ?? prev?.paid,
      balance: inv.balance ?? prev?.balance,
      invoice_date: inv.invoice_date ?? prev?.invoice_date,
      due_date: inv.due_date ?? prev?.due_date,
      customer: data?.customer?.name ?? prev?.customer,
      customer_phone: data?.customer?.phone ?? prev?.customer_phone,
    }));
  };

  const handleRecordPayment = async () => {
    if (!selected?.id || !isBusinessOwner) return;

    setPayError('');
    setPaySuccess('');

    const amount = Number(payAmount);
    if (!amount || amount <= 0) {
      setPayError('Enter a valid payment amount');
      return;
    }

    const balance = Number(selected.balance ?? detail?.invoice?.balance ?? 0);
    if (balance > 0 && amount > balance + 0.001) {
      setPayError(`Amount cannot exceed balance (${balance})`);
      return;
    }

    try {
      setPayLoading(true);
      const data = await invoiceService.recordPayment(selected.id, {
        amount,
        payment_method: payMethod || 'manual',
        note: payNote || 'Recorded from Invoices UI',
      });

      setPaySuccess('Payment recorded successfully');
      setPayAmount('');
      setPayNote('');
      setDetail(data);
      syncSelectedFromDetail(data);
      setLinkInfo(null); // old link amount may be stale
      await loadData();
    } catch (err) {
      const detailMsg = err.response?.data?.detail;
      setPayError(
        typeof detailMsg === 'string'
          ? detailMsg
          : Array.isArray(detailMsg)
            ? detailMsg.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : err.message || 'Failed to record payment'
      );
    } finally {
      setPayLoading(false);
    }
  };

  const handleCustomerPayNow = async () => {
    if (!selected?.id || !isCustomer) return;
    setLinkError('');
    setLinkLoading(true);
    try {
      const data = await paymentService.createLink(selected.id);
      const info = { ...data, invoice_id: data.invoice_id ?? selected.id };
      setLinkInfo(info);
      if (info.url) {
        window.open(info.url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      const detailMsg = err.response?.data?.detail;
      setLinkError(
        typeof detailMsg === 'string'
          ? detailMsg
          : err.message || 'Could not start payment'
      );
    } finally {
      setLinkLoading(false);
    }
  };

  const handleCreatePaymentLink = async () => {
    if (!selected?.id || !isBusinessOwner) return;

    setLinkError('');
    setLinkCopied(false);
    setLinkLoading(true);

    try {
      const data = await paymentService.createLink(selected.id);
      setLinkInfo({
        ...data,
        invoice_id: data.invoice_id ?? selected.id,
      });
    } catch (err) {
      const detailMsg = err.response?.data?.detail;
      setLinkError(
        typeof detailMsg === 'string'
          ? detailMsg
          : Array.isArray(detailMsg)
            ? detailMsg.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : err.message || 'Could not create payment link'
      );
      setLinkInfo(null);
    } finally {
      setLinkLoading(false);
    }
  };

  // Only show link if it belongs to the currently selected invoice
  const activeLink =
    linkInfo && selected && Number(linkInfo.invoice_id) === Number(selected.id)
      ? linkInfo
      : null;

  const copyLink = async () => {
    const url = activeLink?.url;
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch (_) {
      setLinkError('Could not copy — select the URL manually');
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

  const balanceNum = Number(selected?.balance ?? 0);
  const canRecordPayment =
    isBusinessOwner &&
    selected &&
    selected.status !== 'paid' &&
    selected.status !== 'cancelled' &&
    balanceNum > 0;

  const canCreateLink =
    isBusinessOwner &&
    selected &&
    selected.status !== 'paid' &&
    selected.status !== 'cancelled' &&
    balanceNum > 0;

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
          <button
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-tab ${filter === 'overdue' ? 'active' : ''}`}
            onClick={() => setFilter('overdue')}
          >
            Overdue
          </button>
          <button
            className={`filter-tab ${filter === 'partially_paid' ? 'active' : ''}`}
            onClick={() => setFilter('partially_paid')}
          >
            Partial
          </button>
          <button
            className={`filter-tab ${filter === 'sent' ? 'active' : ''}`}
            onClick={() => setFilter('sent')}
          >
            Sent
          </button>
          <button
            className={`filter-tab ${filter === 'paid' ? 'active' : ''}`}
            onClick={() => setFilter('paid')}
          >
            Paid
          </button>
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
                        {(inv.status || '').replace(/_/g, ' ')}
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
              <div className="detail-panel-title">
                {selected.invoice_number || 'Invoice'}
              </div>

              <div className="detail-row">
                <span className="detail-label">Customer</span>
                <span className="detail-value">
                  {detail?.customer?.name || selected.customer || '—'}
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
                    {(selected.status || '').replace(/_/g, ' ')}
                  </span>
                </span>
              </div>

              {detail?.order?.order_number && (
                <div className="detail-row">
                  <span className="detail-label">Order</span>
                  <span className="detail-value">{detail.order.order_number}</span>
                </div>
              )}

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
                  {selected.invoice_date
                    ? String(selected.invoice_date).slice(0, 10)
                    : '—'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Due date</span>
                <span className="detail-value">
                  {selected.due_date ? String(selected.due_date).slice(0, 10) : '—'}
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
                            {/* ===== CUSTOMER: PAY NOW ===== */}
              {isCustomer &&
                selected &&
                selected.status !== 'paid' &&
                selected.status !== 'cancelled' &&
                Number(selected.balance) > 0 && (
                  <>
                    <div className="detail-section-label">Pay online</div>
                    {linkError && (
                      <div style={{ color: '#991b1b', fontSize: 12, marginBottom: 8 }}>
                        {String(linkError)}
                      </div>
                    )}
                    <button
                      type="button"
                      style={btnPrimary}
                      disabled={linkLoading}
                      onClick={handleCustomerPayNow}
                    >
                      {linkLoading
                        ? 'Opening…'
                        : `Pay ${formatMoney(selected.balance)}`}
                    </button>
                    <div style={{ fontSize: 11, color: '#6b7280', marginTop: 8 }}>
                      You will complete payment securely via Razorpay. The invoice
                      updates only after payment is verified.
                    </div>
                    {activeLink?.url && (
                      <div style={{ marginTop: 10, fontSize: 12 }}>
                        <a href={activeLink.url} target="_blank" rel="noreferrer">
                          Open payment page again
                        </a>
                      </div>
                    )}
                  </>
                )}

              {/* ===== RECORD PAYMENT ===== */}
              {canRecordPayment && (
                <>
                  <div className="detail-section-label">Record payment</div>

                  {payError && (
                    <div style={{ color: '#991b1b', fontSize: 12, marginBottom: 8 }}>
                      {String(payError)}
                    </div>
                  )}
                  {paySuccess && (
                    <div style={{ color: '#166534', fontSize: 12, marginBottom: 8 }}>
                      {paySuccess}
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <input
                      className="search-input"
                      type="number"
                      min="1"
                      step="0.01"
                      placeholder={`Amount (max ${selected.balance})`}
                      value={payAmount}
                      onChange={(e) => setPayAmount(e.target.value)}
                    />
                    <select
                      className="search-input"
                      value={payMethod}
                      onChange={(e) => setPayMethod(e.target.value)}
                    >
                      <option value="manual">Manual</option>
                      <option value="cash">Cash</option>
                      <option value="upi">UPI</option>
                      <option value="bank">Bank transfer</option>
                      <option value="razorpay">Razorpay</option>
                    </select>
                    <input
                      className="search-input"
                      type="text"
                      placeholder="Note (optional)"
                      value={payNote}
                      onChange={(e) => setPayNote(e.target.value)}
                    />
                    <button
                      type="button"
                      style={btnPrimary}
                      disabled={payLoading}
                      onClick={handleRecordPayment}
                    >
                      {payLoading ? 'Saving…' : 'Record payment'}
                    </button>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>
                      Partial payments supported. Gateway links use verified capture.
                    </div>
                  </div>
                </>
              )}

              {isBusinessOwner && selected.status === 'paid' && (
                <div style={{ marginTop: 12, fontSize: 12, color: '#166534' }}>
                  Fully paid
                </div>
              )}

              {/* ===== PAYMENT LINK ===== */}
              {canCreateLink && (
                <>
                  <div className="detail-section-label">Payment link</div>

                  {linkError && (
                    <div style={{ color: '#991b1b', fontSize: 12, marginBottom: 8 }}>
                      {String(linkError)}
                    </div>
                  )}

                  {activeLink?.url ? (
                    <div style={{ fontSize: 12, wordBreak: 'break-all' }}>
                      <div style={{ marginBottom: 8 }}>{activeLink.url}</div>
                      <div
                        style={{
                          display: 'flex',
                          gap: 8,
                          flexWrap: 'wrap',
                          alignItems: 'center',
                        }}
                      >
                        <button type="button" onClick={copyLink} style={btnPrimary}>
                          {linkCopied ? 'Copied' : 'Copy link'}
                        </button>
                        <a
                          href={activeLink.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: 13 }}
                        >
                          Open
                        </a>
                        <button
                          type="button"
                          disabled={linkLoading}
                          onClick={handleCreatePaymentLink}
                          style={btnSecondary}
                        >
                          {linkLoading ? 'Creating…' : 'New link'}
                        </button>
                      </div>
                      <div style={{ marginTop: 6, color: '#6b7280', fontSize: 11 }}>
                        Amount locked: {formatMoney(activeLink.amount)}
                        {activeLink.invoice_number
                          ? ` · ${activeLink.invoice_number}`
                          : ''}
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      disabled={linkLoading}
                      onClick={handleCreatePaymentLink}
                      style={btnPrimary}
                    >
                      {linkLoading ? 'Creating…' : 'Create payment link'}
                    </button>
                  )}
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