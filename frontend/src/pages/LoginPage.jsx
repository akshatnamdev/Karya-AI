import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2, Command } from 'lucide-react';
import '../styles/Auth.css';

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');

  const result = await login(formData);

  if (result.success) {
    const role = result.data?.user?.role;
    const redirect =
      result.redirectTo ||
      result.data?.redirect_to ||
      (role === 'platform_admin' ? '/admin' :
       role === 'customer' ? '/portal' :
       '/dashboard');
    navigate(redirect);
  } else {
    setError(typeof result.error === 'string' ? result.error : 'Login failed');
  }

  setLoading(false);
};

  return (
    <div className="auth-page">
      <div className="auth-container">
        
        <div className="auth-header">
          <div className="auth-logo">
            <Command size={20} /> Karya
          </div>
          <h1 className="auth-title">Log in</h1>
          <p className="auth-subtitle">Enter your details to access your workspace.</p>
        </div>
      
        <div className="auth-footer">
          <p style={{ marginBottom: 8 }}>
            Business account?{' '}
            <Link to="/register">Create business account</Link>
          </p>
          <p style={{ margin: 0 }}>
            Ordering from a business?{' '}
            <Link to="/register-customer">Join as customer</Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="name@example.com"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
              className="form-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? <Loader2 size={16} className="spin" /> : 'Log in'}
          </button>
        </form>

        <div className="auth-footer">
          Don't have an account? <Link to="/register">Sign up</Link>
        </div>

      </div>
    </div>
  );
}

export default LoginPage;