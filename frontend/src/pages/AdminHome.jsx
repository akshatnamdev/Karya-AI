import { useEffect, useState, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import adminService from '../services/adminService';
import supportService from '../services/supportService';
import { Loader2, Command, Search, Trash2, Power } from 'lucide-react';
import '../styles/Dashboard.css';
import '../styles/DataPage.css';

function AdminHome() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState('businesses');
  const [stats, setStats] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [users, setUsers] = useState([]);
  const [tickets, setTickets] = useState([]);
  
  const [search, setSearch] = useState('');
  const [selectedBiz, setSelectedBiz] = useState(null);
  const [bizDetail, setBizDetail] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [replyText, setReplyText] = useState('');
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detailLoading, setDetailLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [s, b, u, t] = await Promise.all([
        adminService.stats().catch(() => null),
        adminService.listBusinesses().catch(() => []),
        adminService.listUsers().catch(() => []),
        supportService.list().catch(() => [])
      ]);
      
      if (!s) {
        setError("You do not have permission to view this page or the API failed.");
      } else {
        setStats(s);
        setBusinesses(Array.isArray(b) ? b : []);
        setUsers(Array.isArray(u) ? u : []);
        setTickets(Array.isArray(t) ? t : []);
      }
    } catch (e) {
      console.error("Admin Load Error:", e);
      setError('Failed to load admin data. Check backend logs.');
    } finally {
      setLoading(false);
    }
  };

  const openBusiness = async (b) => {
    setSelectedBiz(b);
    setDetailLoading(true);
    setBizDetail(null);
    try {
      const d = await adminService.businessDetail(b.id);
      setBizDetail(d);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const toggleBusinessStatus = async (b) => {
    const currentActive = bizDetail?.business?.is_active ?? b.is_active;
    const action = currentActive ? 'disable' : 'enable';
    if (!window.confirm(`Are you sure you want to ${action} "${b.name}"? This will ${action} all user access for this business.`)) return;
    
    setBusy(true);
    try {
      await adminService.setBusinessActive(b.id, !currentActive);
      await loadData();
      if (selectedBiz?.id === b.id) {
        const updatedDetail = await adminService.businessDetail(b.id);
        setBizDetail(updatedDetail);
      }
    } catch (e) {
      console.error(e);
      alert(`Failed to ${action} business.`);
    } finally {
      setBusy(false);
    }
  };

  const deleteBiz = async (b) => {
    if (!window.confirm(`⚠️ Are you sure you want to PERMANENTLY delete "${b.name}"? This removes all associated data.`)) return;
    setBusy(true);
    try {
      await adminService.deleteBusiness(b.id);
      setSelectedBiz(null);
      setBizDetail(null);
      await loadData();
    } catch (e) {
      console.error(e);
      alert("Failed to delete business.");
    } finally {
      setBusy(false);
    }
  };

  const toggleUser = async (u) => {
    setBusy(true);
    try {
      await adminService.setUserActive(u.id, !u.is_active);
      const list = await adminService.listUsers();
      setUsers(list);
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  const openTicket = async (t) => {
    setSelectedTicket(t);
    setDetailLoading(true);
    try {
      const d = await supportService.get(t.id);
      setTicketDetail(d);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleTicketReply = async () => {
    if (!replyText.trim()) return;
    setBusy(true);
    try {
      const updated = await supportService.reply(selectedTicket.id, replyText);
      setTicketDetail(updated);
      setReplyText('');
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  const handleTicketResolve = async () => {
    setBusy(true);
    try {
      const updated = await supportService.resolve(selectedTicket.id);
      setTicketDetail(updated);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  const filteredBusinesses = useMemo(() => {
    if (!search) return businesses;
    const q = search.toLowerCase();
    return businesses.filter(b => 
      b.name?.toLowerCase().includes(q) || 
      b.owner_name?.toLowerCase().includes(q) ||
      b.city?.toLowerCase().includes(q)
    );
  }, [businesses, search]);

  const filteredUsers = useMemo(() => {
    if (!search) return users;
    const q = search.toLowerCase();
    return users.filter(u => 
      u.name?.toLowerCase().includes(q) || 
      u.email?.toLowerCase().includes(q) ||
      u.business_name?.toLowerCase().includes(q)
    );
  }, [users, search]);

  const filteredTickets = useMemo(() => {
    if (!search) return tickets;
    const q = search.toLowerCase();
    return tickets.filter(t => 
      t.subject?.toLowerCase().includes(q) || 
      t.opened_by?.name?.toLowerCase().includes(q)
    );
  }, [tickets, search]);

  const money = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`;
  const formatDate = (d) => d ? new Date(d).toLocaleDateString() : '—';

  if (loading) {
    return <div className="loading-box"><Loader2 size={24} className="spin" /></div>;
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f8f9fa' }}>
      <header style={{
        background: '#fff', borderBottom: '1px solid #e5e7eb',
        padding: '14px 24px', display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', position: 'sticky', top: 0, zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 16, color: '#111827' }}>
          <Command size={18} /> Karya Platform Admin
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: 13 }}>
          <span style={{ color: '#4b5563', fontWeight: 500 }}>{user?.email}</span>
          <button onClick={logout} style={{
            border: '1px solid #e5e7eb', background: '#fff', padding: '6px 14px',
            borderRadius: 6, cursor: 'pointer', fontSize: 13, color: '#dc2626', fontWeight: 500
          }}>
            Log out
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '32px 24px' }}>
        <h1 className="page-title">Platform Overview</h1>
        <p className="page-subtitle" style={{marginBottom: 32}}>God-mode view of the entire Karya AI ecosystem.</p>

        {error && <div style={{ background: '#fef2f2', color: '#991b1b', padding: 12, borderRadius: 6, marginBottom: 20 }}>{error}</div>}

        {stats && (
          <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginBottom: 40 }}>
            <div className="metric-item"><span className="metric-label">Total Businesses</span><span className="metric-value">{stats.total_businesses}</span></div>
            <div className="metric-item"><span className="metric-label">Total Users</span><span className="metric-value">{stats.total_users}</span></div>
            <div className="metric-item"><span className="metric-label">Platform Revenue</span><span className="metric-value">{money(stats.total_revenue)}</span></div>
            <div className="metric-item"><span className="metric-label">Platform Outstanding</span><span className="metric-value" style={{color: '#dc2626'}}>{money(stats.total_outstanding)}</span></div>
            <div className="metric-item"><span className="metric-label">Total Customers</span><span className="metric-value">{stats.total_customers}</span></div>
            <div className="metric-item"><span className="metric-label">Total Orders</span><span className="metric-value">{stats.total_orders}</span></div>
            <div className="metric-item"><span className="metric-label">Total Invoices</span><span className="metric-value">{stats.total_invoices}</span></div>
            <div className="metric-item"><span className="metric-label">Open Tickets</span><span className="metric-value">{stats.open_tickets || tickets.filter(t => t.status === 'open').length}</span></div>
          </div>
        )}

        <div className="page-toolbar">
          <div style={{ position: 'relative', width: '300px' }}>
            <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: '#9ca3af' }} />
            <input 
              className="search-input" 
              style={{ paddingLeft: 34, width: '100%' }}
              placeholder={`Search ${tab}...`} 
              value={search} onChange={(e) => setSearch(e.target.value)} 
            />
          </div>
          <div className="filter-tabs">
            <button className={`filter-tab ${tab === 'businesses' ? 'active' : ''}`} onClick={() => { setTab('businesses'); setSearch(''); }}>
              Businesses ({businesses.length})
            </button>
            <button className={`filter-tab ${tab === 'users' ? 'active' : ''}`} onClick={() => { setTab('users'); setSearch(''); }}>
              Users ({users.length})
            </button>
            <button className={`filter-tab ${tab === 'support' ? 'active' : ''}`} onClick={() => { setTab('support'); setSearch(''); }}>
              Support Requests ({tickets.length})
            </button>
          </div>
        </div>

        {/* Tab Content: Businesses */}
        {tab === 'businesses' && (
          <div className="detail-layout" style={{ gridTemplateColumns: '1fr 380px' }}>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Business Name</th>
                    <th>Owner</th>
                    <th>City</th>
                    <th className="right">Users</th>
                    <th className="right">Customers</th>
                    <th className="right">Orders</th>
                    <th className="right">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBusinesses.map(b => (
                    <tr key={b.id} className={selectedBiz?.id === b.id ? 'selected' : ''} onClick={() => openBusiness(b)}>
                      <td className="cell-mono">{b.id}</td>
                      <td className="cell-primary">
                        {b.name}
                        {!b.is_active && <span style={{ marginLeft: 6, fontSize: 10, color: '#dc2626', fontWeight: 600 }}>(DISABLED)</span>}
                      </td>
                      <td>{b.owner_name}</td>
                      <td className="cell-muted">{b.city}</td>
                      <td className="right">{b.users}</td>
                      <td className="right">{b.customers}</td>
                      <td className="right">{b.orders}</td>
                      <td className="right cell-primary">{money(b.revenue)}</td>
                    </tr>
                  ))}
                  {filteredBusinesses.length === 0 && (
                    <tr><td colSpan="8" style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>No businesses found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <aside className="detail-panel" style={{ background: '#f8f9fa' }}>
              {!selectedBiz ? (
                <div className="detail-empty" style={{ textAlign: 'center', padding: 40 }}>Select a business to view Deep Insights</div>
              ) : detailLoading ? (
                <div style={{ padding: 40, textAlign: 'center' }}><Loader2 size={24} className="spin" /></div>
              ) : bizDetail ? (
                <>
                  <div className="detail-panel-title" style={{ fontSize: 18, borderBottom: '2px solid #e5e7eb' }}>
                    {bizDetail.business.name}
                  </div>
                  
                  <div className="detail-section-label">General Info</div>
                  <div className="detail-row">
                    <span className="detail-label">Status</span>
                    <span className="status-pill">
                      <span className={`status-dot ${bizDetail.business.is_active ? 'green' : 'red'}`}/>
                      {bizDetail.business.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                  <div className="detail-row"><span className="detail-label">Type</span><span className="detail-value">{bizDetail.business.type || '—'}</span></div>
                  <div className="detail-row"><span className="detail-label">Location</span><span className="detail-value">{bizDetail.business.city || '—'}</span></div>
                  
                  <div className="detail-section-label">Owner Information</div>
                  <div className="detail-row"><span className="detail-label">Name</span><span className="detail-value cell-primary">{bizDetail.owner.name}</span></div>
                  <div className="detail-row"><span className="detail-label">Email</span><span className="detail-value">{bizDetail.owner.email}</span></div>
                  <div className="detail-row"><span className="detail-label">Phone</span><span className="detail-value">{bizDetail.owner.phone}</span></div>

                  <div className="detail-section-label">Usage Metrics</div>
                  <div className="detail-row"><span className="detail-label">Total Users</span><span className="detail-value">{bizDetail.counts.users}</span></div>
                  <div className="detail-row"><span className="detail-label">Customers</span><span className="detail-value">{bizDetail.counts.customers}</span></div>
                  <div className="detail-row"><span className="detail-label">Products</span><span className="detail-value">{bizDetail.counts.products}</span></div>
                  <div className="detail-row"><span className="detail-label">Orders</span><span className="detail-value">{bizDetail.counts.orders}</span></div>

                  <div className="detail-section-label">Financials</div>
                  <div className="detail-row"><span className="detail-label">Total Revenue</span><span className="detail-value cell-primary">{money(bizDetail.financials.revenue)}</span></div>
                  <div className="detail-row"><span className="detail-label">Total Outstanding</span><span className="detail-value" style={{color: '#dc2626'}}>{money(bizDetail.financials.outstanding)}</span></div>

                  {/* Actions Area */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 24 }}>
                    <button 
                      onClick={() => toggleBusinessStatus(selectedBiz)} 
                      disabled={busy} 
                      style={{
                        width: '100%', 
                        padding: '10px', 
                        background: bizDetail.business.is_active ? '#fff7ed' : '#f0fdf4', 
                        color: bizDetail.business.is_active ? '#c2410c' : '#15803d', 
                        border: `1px solid ${bizDetail.business.is_active ? '#ffedd5' : '#bbf7d0'}`, 
                        borderRadius: 6, 
                        fontWeight: 500, 
                        cursor: busy ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6
                      }}
                    >
                      <Power size={16} /> {bizDetail.business.is_active ? 'Disable Business Access' : 'Enable Business Access'}
                    </button>

                    <button 
                      onClick={() => deleteBiz(selectedBiz)} 
                      disabled={busy} 
                      style={{
                        width: '100%', 
                        padding: '10px', 
                        background: '#fef2f2', 
                        color: '#dc2626', 
                        border: '1px solid #fecaca', 
                        borderRadius: 6, 
                        fontWeight: 500, 
                        cursor: busy ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6
                      }}
                    >
                      <Trash2 size={16} /> Delete Business & Data
                    </button>
                  </div>
                </>
              ) : null}
            </aside>
          </div>
        )}

        {/* Tab Content: Users */}
        {tab === 'users' && (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Assigned Business</th>
                  <th>Joined Date</th>
                  <th>Status</th>
                  <th className="right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(u => {
                  const isAdmin = u.role?.toLowerCase().includes('admin') || u.email === user?.email;
                  return (
                    <tr key={u.id}>
                      <td className="cell-mono">{u.id}</td>
                      <td className="cell-primary">{u.name}</td>
                      <td className="cell-muted">{u.email}</td>
                      <td><span className="status-pill">{u.role}</span></td>
                      <td>{u.business_name}</td>
                      <td className="cell-muted">{formatDate(u.created_at)}</td>
                      <td>
                        <span className="status-pill">
                          <span className={`status-dot ${u.is_active ? 'green' : 'red'}`}/>
                          {u.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </td>
                      <td className="right">
                        <button
                          onClick={() => toggleUser(u)}
                          disabled={busy || isAdmin}
                          style={{
                            border: '1px solid #e5e7eb', 
                            padding: '4px 10px',
                            borderRadius: 4, 
                            background: isAdmin ? '#f3f4f6' : '#fff',
                            color: isAdmin ? '#9ca3af' : '#111827',
                            fontSize: 12, 
                            cursor: isAdmin ? 'not-allowed' : 'pointer'
                          }}
                        >
                          {u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Tab Content: Support Requests */}
        {tab === 'support' && (
          <div className="detail-layout" style={{ gridTemplateColumns: '1fr 400px' }}>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Subject</th>
                    <th>Opened By</th>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTickets.map(t => (
                    <tr key={t.id} className={selectedTicket?.id === t.id ? 'selected' : ''} onClick={() => openTicket(t)}>
                      <td className="cell-mono">{t.id}</td>
                      <td className="cell-primary">{t.subject}</td>
                      <td>{t.opened_by?.name || "Unknown"}</td>
                      <td className="cell-muted">{t.opened_by?.role || "—"}</td>
                      <td>
                        <span className="status-pill">
                          <span className={`status-dot ${t.status === 'open' ? 'amber' : t.status === 'resolved' ? 'green' : 'red'}`} />
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {filteredTickets.length === 0 && (
                    <tr><td colSpan="5" style={{textAlign:'center', padding: 40, color: '#9ca3af'}}>No support tickets found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            
            <aside className="detail-panel" style={{ background: '#f8f9fa' }}>
              {!selectedTicket ? (
                <div className="detail-empty" style={{ textAlign: 'center', padding: 40 }}>Select a ticket to manage</div>
              ) : detailLoading ? (
                <div style={{ padding: 40, textAlign: 'center' }}><Loader2 size={24} className="spin" /></div>
              ) : ticketDetail ? (
                <>
                  <div className="detail-panel-title" style={{ fontSize: 16 }}>{ticketDetail.subject}</div>
                  <div className="detail-row"><span className="detail-label">Status</span><span className="detail-value">{ticketDetail.status}</span></div>
                  <div className="detail-row"><span className="detail-label">Opened By</span><span className="detail-value">{ticketDetail.opened_by?.name}</span></div>
                  <div className="detail-row"><span className="detail-label">Date</span><span className="detail-value">{formatDate(ticketDetail.created_at)}</span></div>
                  
                  <div className="detail-section-label" style={{marginTop: 20}}>Conversation Log</div>
                  <div style={{ maxHeight: 300, overflowY: 'auto', padding: 10, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 6}}>
                    {ticketDetail.messages?.map(m => (
                      <div key={m.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid #f3f4f6' }}>
                        <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4, fontWeight: 600 }}>
                          {m.sender_role.toUpperCase()}
                        </div>
                        <div style={{ fontSize: 13, color: '#111827' }}>{m.body}</div>
                      </div>
                    ))}
                  </div>
                  
                  {ticketDetail.status !== 'resolved' && (
                    <div style={{ marginTop: 20 }}>
                      <textarea 
                        style={{ width: '100%', padding: 10, border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13, minHeight: 80, resize: 'none' }}
                        placeholder="Type reply to customer/business..."
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                      />
                      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                        <button 
                          onClick={handleTicketReply}
                          disabled={busy || !replyText}
                          style={{ flex: 1, padding: '8px', background: '#111827', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}
                        >
                          Send Reply
                        </button>
                        <button 
                          onClick={handleTicketResolve}
                          disabled={busy}
                          style={{ padding: '8px 16px', background: '#fff', border: '1px solid #d1d5db', color: '#374151', borderRadius: 6, cursor: 'pointer' }}
                        >
                          Mark Resolved
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : null}
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}

export default AdminHome;