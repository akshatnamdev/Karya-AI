import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Brain, User, Mail, Lock, Phone, Building2, MapPin, Loader2 } from 'lucide-react';
import '../styles/Auth.css';

function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    business_name: '',
    business_type: 'wholesaler',
    city: '', // Added city field
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await register(formData);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-wrapper">
        
        <div className="auth-header">
          <div className="auth-logo">
            <Brain size={32} color="#ffffff" />
          </div>
          <h1 className="auth-title">Create Account</h1>
          <p className="auth-subtitle">
            Create your business account
          </p>
        </div>

        <div className="auth-card">
          <form onSubmit={handleSubmit} className="auth-form">

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div className="form-input-wrapper">
                <User className="form-input-icon" size={18} />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  minLength={2}
                  placeholder="Akshat Namdev"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className="form-input-wrapper">
                <Mail className="form-input-icon" size={18} />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  placeholder="you@example.com"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="form-input-wrapper">
                <Lock className="form-input-icon" size={18} />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  minLength={6}
                  placeholder="Minimum 6 characters"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <div className="form-input-wrapper">
                <Phone className="form-input-icon" size={18} />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="9876543210"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Business Name</label>
              <div className="form-input-wrapper">
                <Building2 className="form-input-icon" size={18} />
                <input
                  type="text"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleChange}
                  placeholder="Your Business Name"
                  className="form-input"
                />
              </div>
            </div>

            {/* City / Location Field */}
            <div className="form-group">
              <label className="form-label">City / Location</label>
              <div className="form-input-wrapper">
                <MapPin className="form-input-icon" size={18} />
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  placeholder="e.g. Bhopal, Indore, Mumbai"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Business Type</label>
              <select
                name="business_type"
                value={formData.business_type}
                onChange={handleChange}
                className="form-select"
              >
                <option value="wholesaler">Wholesaler</option>
                <option value="pharmacy_wholesaler">Pharmacy Wholesaler</option>
                <option value="retailer">Retailer</option>
                <option value="distributor">Distributor</option>
                <option value="manufacturer">Manufacturer</option>
              </select>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </button>

          </form>

          <div className="auth-footer">
            Already have an account?{' '}
            <Link to="/login">Sign in here</Link>
          </div>
        </div>

      </div>
    </div>
  );
}

export default RegisterPage;