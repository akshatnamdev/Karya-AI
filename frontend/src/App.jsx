import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CustomerRegisterPage from './pages/CustomerRegisterPage';
import DashboardPage from './pages/DashboardPage';
import AssistantPage from './pages/AssistantPage';
import CustomersPage from './pages/CustomersPage';
import ProductsPage from './pages/ProductsPage';
import OrdersPage from './pages/OrdersPage';
import InvoicesPage from './pages/InvoicesPage';
import AdminHome from './pages/AdminHome';
import PortalHome from './pages/PortalHome';
import SupportPage from './pages/SupportPage';


function RoleRoute({ children, allow }) {
  const { user, isAuthenticated } = useAuth();
    <Route path="/support" element={
  <RoleRoute allow={['business_owner', 'customer', 'platform_admin']}>
  <a href="/support" style={{ color: '#111827', fontSize: 13, marginRight: 12 }}>Support</a>
    <SupportPage />
  </RoleRoute>
} />
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const role = user?.role;
  if (allow && !allow.includes(role)) {
    const homeMap = {
      platform_admin: '/admin',
      business_owner: '/dashboard',
      customer: '/portal',
    };
    return <Navigate to={homeMap[role] || '/login'} replace />;
  }

  return children;
}

function PublicRoute({ children }) {
  const { user, isAuthenticated } = useAuth();

  if (isAuthenticated) {
    const homeMap = {
      platform_admin: '/admin',
      business_owner: '/dashboard',
      customer: '/portal',
    };
    return <Navigate to={homeMap[user?.role] || '/dashboard'} replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/register-customer" element={<PublicRoute><CustomerRegisterPage /></PublicRoute>} />

      {/* Business owner */}
      <Route path="/dashboard" element={<RoleRoute allow={['business_owner']}><DashboardPage /></RoleRoute>} />
      <Route path="/assistant" element={<RoleRoute allow={['business_owner', 'customer']}><AssistantPage /></RoleRoute>} />
      <Route path="/customers" element={<RoleRoute allow={['business_owner']}><CustomersPage /></RoleRoute>} />
      <Route path="/products" element={<RoleRoute allow={['business_owner', 'customer']}><ProductsPage /></RoleRoute>} />
      <Route path="/orders" element={<RoleRoute allow={['business_owner', 'customer']}><OrdersPage /></RoleRoute>} />
      <Route path="/invoices" element={<RoleRoute allow={['business_owner', 'customer']}><InvoicesPage /></RoleRoute>} />

      {/* Admin — own layout inside page */}
      <Route path="/admin" element={<RoleRoute allow={['platform_admin']}><AdminHome /></RoleRoute>} />

      {/* Customer portal */}
      <Route path="/portal" element={<RoleRoute allow={['customer']}><PortalHome /></RoleRoute>} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;