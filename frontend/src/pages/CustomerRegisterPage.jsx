import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Command, Loader2 } from 'lucide-react';
import api from '../services/api';
import '../styles/Auth.css';

function CustomerRegisterPage() {
  const navigate = useNavigate();
  const { registerCustomer } = useAuth();

  const [businesses, setBusinesses] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    business_id: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingBiz, setLoadingBiz] = useState(true);

  useEffect(() => {
    // Fetch public list of businesses for dropdown
    api
      .get('/api/public/businesses')
      .then((res) => {
        const list = Array.isArray(res.data)
          ? res.data
          : res.data?.businesses || res.data?.data || [];
        setBusinesses(list);

        if (list.length > 0) {
          setFormData((f) => ({ ...f, business_id: String(list[0].id) }));
        }
      })
      .catch((err) => {
        console.error('Failed to load businesses:', err);
        setError('Could not load businesses list. Please refresh the page.');
      })
      .finally(() => setLoadingBiz(false));
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!formData.business_id) {
      setError('Please select a business to order from.');
      setLoading(false);
      return;
    }

    const payload = {
      name: formData.name.trim(),
      email: formData.email.trim().toLowerCase(),
      password: formData.password,
      phone: formData.phone.trim() || null,
      business_id: Number(formData.business_id),
    };

    try {
      const result = await registerCustomer(payload);

      if (result && result.success) {
        navigate(result.redirectTo || result.data?.redirect_to || '/portal');
        return;
      }

      // Prefer real backend message
      const raw = result?.error;
      let msg = 'Registration failed.';
      if (typeof raw === 'string') msg = raw;
      else if (raw?.detail) msg = typeof raw.detail === 'string' ? raw.detail : JSON.stringify(raw.detail);
      else if (raw?.message) msg = raw.message;
      setError(msg);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      let msg = 'Registration failed.';
      if (typeof detail === 'string') msg = detail;
      else if (Array.isArray(detail)) msg = detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      else if (err?.message) msg = err.message;
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="auth-logo">
            <Command size={20} /> Karya
          </div>
          <h1 className="auth-title">Join as customer</h1>
          <p className="auth-subtitle">
            Create an account to order from a business on Karya.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Business you order from</label>
            {loadingBiz ? (
              <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0' }}>
                Loading available businesses...
              </p>
            ) : (
              <select
                name="business_id"
                value={formData.business_id}
                onChange={handleChange}
                required
                className="form-select"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  backgroundColor: '#ffffff',
                  fontSize: '14px',
                  color: '#111827',
                }}
              >
                <option value="">Select a business...</option>
                {businesses.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} {b.city ? `(${b.city})` : ''}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Your name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              minLength={2}
              className="form-input"
              style={{ paddingLeft: 12 }}
              placeholder="Your full name"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input"
              style={{ paddingLeft: 12 }}
              placeholder="you@example.com"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Phone</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
              className="form-input"
              style={{ paddingLeft: 12 }}
              placeholder="9876543210"
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
              minLength={6}
              className="form-input"
              style={{ paddingLeft: 12 }}
              placeholder="Minimum 6 characters"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading || loadingBiz} className="btn-primary">
            {loading ? <Loader2 size={16} className="spin" /> : 'Create customer account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
          <br />
          Own a business? <Link to="/register">Create business account</Link>
        </div>
      </div>
    </div>
  );
}

export default CustomerRegisterPage;