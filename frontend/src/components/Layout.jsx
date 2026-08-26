import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Command } from 'lucide-react';
import '../styles/Layout.css';

function Layout({ children }) {
  const { user, logout, isPlatformAdmin, isBusinessOwner, isCustomer } = useAuth();

  // Build nav items based on role
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
      { path: '/support', label: 'Support' },
      { path: '/support', label: 'Support' },
    );
  }
  
  if (isCustomer) {
    navItems.push(
      { path: '/portal', label: 'Home' },
      { path: '/products', label: 'Catalog' },
      { path: '/orders', label: 'My Orders' },
      { path: '/invoices', label: 'My Invoices' },
      { path: '/assistant', label: 'Assistant' },
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
          
          <div className="nav-left">
            <div className="nav-brand">
              <Command size={16} /> Karya
              {roleLabel && (
                <span style={{
                  fontSize: 11,
                  fontWeight: 500,
                  color: '#6b7280',
                  padding: '2px 6px',
                  border: '1px solid #e5e7eb',
                  borderRadius: 4,
                  marginLeft: 8,
                }}>{roleLabel}</span>
              )}
            </div>
            <nav className="nav-links">
              {navItems.map(item => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({isActive}) => isActive ? "nav-link active" : "nav-link"}
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="nav-right">
            <div className="user-menu">{user?.name}</div>
            <button onClick={logout} className="logout-btn">Log out</button>
          </div>

        </div>
      </header>
      
      <main className="main-container">
        {children}
      </main>
    </div>
  );
}

export default Layout;