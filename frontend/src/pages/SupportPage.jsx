import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import supportService from '../services/supportService';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';
import '../styles/DataPage.css';

function SupportPage() {
  const { user, isCustomer, isBusinessOwner, isPlatformAdmin } = useAuth();

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [reply, setReply] = useState('');
  const [newSubject, setNewSubject] = useState('');
  const [newBody, setNewBody] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const t = await supportService.list();
      setTickets(t);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const open = async (t) => {
    setSelected(t);
    setDetail(null);
    setReply('');
    try {
      setDetail(await supportService.get(t.id));
    } catch (e) { console.error(e); }
  };

  const sendReply = async () => {
    if (!reply.trim()) return;
    setBusy(true);
    try {
      setDetail(await supportService.reply(selected.id, reply.trim()));
      setReply('');
      load();
    } finally {
      setBusy(false);
    }
  };

  const create = async () => {
    if (!newSubject.trim() || !newBody.trim()) return;
    setBusy(true);
    try {
      const t = await supportService.create(newSubject.trim(), newBody.trim());
      setNewSubject(''); setNewBody(''); setShowNew(false);
      await load();
      open(t);
    } finally {
      setBusy(false);
    }
  };

  const escalate = async () => {
    setBusy(true);
    try { setDetail(await supportService.escalate(selected.id)); await load(); }
    finally { setBusy(false); }
  };

  const resolve = async () => {
    setBusy(true);
    try { setDetail(await supportService.resolve(selected.id)); await load(); }
    finally { setBusy(false); }
  };

  const content = (
    <>
      <header className="page-header">
        <h1 className="page-title">Support</h1>
        <p className="page-subtitle">
          {isCustomer && 'Ask the business for help.'}
          {isBusinessOwner && 'Help your customers and escalate to Karya admin when needed.'}
          {isPlatformAdmin && 'All escalated tickets across the platform.'}
        </p>
      </header>

      {(isCustomer || isBusinessOwner) && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={() => setShowNew(v => !v)}
            style={{
              padding: '8px 14px',
              background: '#111827', color: '#fff',
              border: 'none', borderRadius: 6,
              fontSize: 13, cursor: 'pointer',
            }}
          >
            {showNew ? 'Cancel' : 'New ticket'}
          </button>
        </div>
      )}

      {showNew && (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: 6, padding: 16, marginBottom: 24 }}>
          <input
            className="search-input"
            style={{ width: '100%', marginBottom: 8 }}
            placeholder="Subject"
            value={newSubject}
            onChange={(e) => setNewSubject(e.target.value)}
          />
          <textarea
            style={{
              width: '100%', padding: 10, border: '1px solid #d1d5db',
              borderRadius: 6, minHeight: 100, fontFamily: 'inherit', fontSize: 13,
            }}
            placeholder="Describe your issue..."
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
          />
          <button
            onClick={create}
            disabled={busy}
            style={{
              marginTop: 8, padding: '6px 14px',
              background: '#111827', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13,
            }}
          >
            Create ticket
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading-box"><Loader2 size={16} className="spin" /></div>
      ) : (
        <div className="detail-layout">
          <div className="data-table-wrap">
            {tickets.length === 0 ? (
              <div className="empty-state-box">No tickets yet</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Subject</th>
                    <th>Opened by</th>
                    <th>Status</th>
                    <th>Assigned</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map(t => (
                    <tr
                      key={t.id}
                      onClick={() => open(t)}
                      className={selected?.id === t.id ? 'selected' : ''}
                    >
                      <td className="cell-mono">{t.id}</td>
                      <td className="cell-primary">{t.subject}</td>
                      <td className="cell-muted">{t.opened_by.name}</td>
                      <td>
                        <span className="status-pill">
                          <span className={`status-dot ${
                            t.status === 'open' ? 'amber' :
                            t.status === 'pending_admin' ? 'red' : 'green'
                          }`}></span>
                          {t.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="cell-muted">{t.assigned_to_role.replace('_', ' ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <aside className="detail-panel">
            {!selected ? (
              <div className="detail-empty">Select a ticket</div>
            ) : !detail ? (
              <Loader2 size={16} className="spin" />
            ) : (
              <>
                <div className="detail-panel-title">{detail.subject}</div>
                <div className="detail-row">
                  <span className="detail-label">Status</span>
                  <span className="detail-value">{detail.status.replace('_', ' ')}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Opened by</span>
                  <span className="detail-value">{detail.opened_by.name}</span>
                </div>

                <div className="detail-section-label">Conversation</div>
                <div style={{
                  maxHeight: 320, overflowY: 'auto',
                  border: '1px solid #f3f4f6', borderRadius: 6,
                  padding: 8, background: '#fafafa',
                }}>
                  {detail.messages.map(m => (
                    <div key={m.id} style={{
                      display: 'flex',
                      justifyContent: m.sender_id === user.id ? 'flex-end' : 'flex-start',
                      marginBottom: 8,
                    }}>
                      <div style={{
                        maxWidth: '85%',
                        background: m.sender_id === user.id ? '#111827' : '#fff',
                        color: m.sender_id === user.id ? '#fff' : '#111827',
                        padding: '8px 12px',
                        borderRadius: 6,
                        fontSize: 13,
                        border: m.sender_id === user.id ? 'none' : '1px solid #e5e7eb',
                      }}>
                        <div style={{
                          fontSize: 10,
                          opacity: 0.7,
                          marginBottom: 4,
                          textTransform: 'uppercase',
                        }}>
                          {m.sender_role.replace('_', ' ')}
                        </div>
                        {m.body}
                      </div>
                    </div>
                  ))}
                </div>

                {detail.status !== 'resolved' && (
                  <>
                    <textarea
                      style={{
                        width: '100%', marginTop: 12,
                        padding: 8, border: '1px solid #d1d5db',
                        borderRadius: 6, minHeight: 60, fontFamily: 'inherit', fontSize: 13,
                      }}
                      placeholder="Type a reply..."
                      value={reply}
                      onChange={(e) => setReply(e.target.value)}
                    />
                    <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                      <button
                        onClick={sendReply}
                        disabled={busy || !reply.trim()}
                        style={{
                          flex: 1, padding: '6px 10px',
                          background: '#111827', color: '#fff',
                          border: 'none', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                        }}
                      >
                        Send
                      </button>
                      {isBusinessOwner && detail.assigned_to_role === 'business_owner' && (
                        <button
                          onClick={escalate}
                          disabled={busy}
                          style={{
                            padding: '6px 10px', background: '#fff',
                            border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 12,
                            cursor: 'pointer',
                          }}
                        >
                          Escalate to admin
                        </button>
                      )}
                      <button
                        onClick={resolve}
                        disabled={busy}
                        style={{
                          padding: '6px 10px', background: '#fff',
                          border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 12,
                          cursor: 'pointer',
                        }}
                      >
                        Resolve
                      </button>
                    </div>
                  </>
                )}
              </>
            )}
          </aside>
        </div>
      )}
    </>
  );

  if (isPlatformAdmin) {
    // Admin uses plain wrapper (no business Layout nav)
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
        {content}
      </div>
    );
  }

  return <Layout>{content}</Layout>;
}

export default SupportPage;