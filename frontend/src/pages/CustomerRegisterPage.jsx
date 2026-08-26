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
    // Public list of businesses to join (we'll add this API)
    api
      .get('/api/public/businesses')
      .then((res) => {
        setBusinesses(res.data || []);
        if (res.data?.length === 1) {
          setFormData((f) => ({ ...f, business_id: String(res.data[0].id) }));
        }
      })
      .catch(() => {
        // Fallback: allow manual business_id
        setBusinesses([]);
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
      name: formData.name,
      email: formData.email,
      password: formData.password,
      phone: formData.phone,
      business_id: Number(formData.business_id),
    };

    const result = await registerCustomer(payload);

    if (result.success) {
      navigate(result.redirectTo || result.data?.redirect_to || '/portal');
    } else {
      setError(typeof result.error === 'string' ? result.error : 'Registration failed');
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
          <h1 className="auth-title">Join as customer</h1>
          <p className="auth-subtitle">
            Create an account to order from a business on Karya.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Business you order from</label>
            {loadingBiz ? (
              <p style={{ fontSize: 13, color: '#6b7280' }}>Loading businesses...</p>
            ) : businesses.length > 0 ? (
              <select
                name="business_id"
                value={formData.business_id}
                onChange={handleChange}
                required
                className="form-select"
              >
                <option value="">Select business</option>
                {businesses.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} {b.city ? `(${b.city})` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                name="business_id"
                value={formData.business_id}
                onChange={handleChange}
                required
                placeholder="Business ID (ask the shop)"
                className="form-input"
                style={{ paddingLeft: 12 }}
              />
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

          <button type="submit" disabled={loading} className="btn-primary">
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