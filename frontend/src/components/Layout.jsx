import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Command } from 'lucide-react';
import api from '../services/api';
import '../styles/Layout.css';

function Layout({ children }) {
  const { user, logout, isPlatformAdmin, isBusinessOwner, isCustomer } = useAuth();

  const [joinedBusinesses, setJoinedBusinesses] = useState([]);
  const [activeBusinessId, setActiveBusinessId] = useState(
    localStorage.getItem('karya_active_business_id') || ''
  );

  useEffect(() => {
    if (isCustomer) {
      api.get('/api/customers/my-businesses')
        .catch(() => api.get('/api/my-businesses'))
        .then((res) => {
          const list = Array.isArray(res.data) ? res.data : [];
          setJoinedBusinesses(list);
          if (list.length > 0 && !activeBusinessId) {
            const firstId = String(list[0].business_id);
            setActiveBusinessId(firstId);
            localStorage.setItem('karya_active_business_id', firstId);
          }
        })
        .catch((err) => console.error('Failed to load joined businesses:', err));
    }
  }, [isCustomer]);

  const handleBusinessSwitch = (e) => {
    const newBizId = e.target.value;
    setActiveBusinessId(newBizId);
    localStorage.setItem('karya_active_business_id', newBizId);
    window.location.reload();
  };

  const navItems = [];

  if (isPlatformAdmin) {
    navItems.push({ path: '/admin', label: 'Overview' });
  }

  if (isBusinessOwner) {
    navItems.push(
      { path: '/dashboard', label: 'Overview' },
      { path: '/customers', label: 'Customers' },
      { path: '/products', label: 'Inventory' },
      { path: '/orders', label: 'Orders' },
      { path: '/invoices', label: 'Invoices' },
      { path: '/assistant', label: 'Assistant' },
      { path: '/support', label: 'Support' }
    );
  }

  if (isCustomer) {
    navItems.push(
      { path: '/portal', label: 'Home' },
      { path: '/products', label: 'Catalog' },
      { path: '/orders', label: 'My Orders' },
      { path: '/invoices', label: 'My Invoices' },
      { path: '/assistant', label: 'Assistant' },
      { path: '/support', label: 'Support' }
    );
  }

  const roleLabel = {
    platform_admin: 'Admin',
    business_owner: 'Business',
    customer: 'Customer',
  }[user?.role] || '';

  return (
    <div className="app-layout">
      <header className="top-nav">
        <div className="nav-container">
          {/* LEFT: brand + role + business switcher */}
          <div className="nav-left">
            <div className="nav-brand">
              <Command size={16} />
              <span className="brand-text">Karya</span>
              {roleLabel && <span className="role-badge">{roleLabel}</span>}
            </div>

            {isCustomer && joinedBusinesses.length > 0 && (
              <div className="business-switcher-wrap">
                <select
                  className="business-switcher"
                  value={activeBusinessId}
                  onChange={handleBusinessSwitch}
                  aria-label="Switch business"
                >
                  {joinedBusinesses.map((b) => (
                    <option key={b.business_id} value={b.business_id}>
                      {b.business_name}
                      {b.city ? ` (${b.city})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* CENTER: main links */}
          <nav className="nav-links">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* RIGHT: user + logout only */}
          <div className="nav-right">
            <span className="user-menu">{user?.name}</span>
            <button type="button" onClick={logout} className="logout-btn">
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="main-container">{children}</main>
    </div>
  );
}

export default Layout;