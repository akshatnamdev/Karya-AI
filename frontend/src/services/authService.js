import api from './api';

export const authService = {
  async register(userData) {
    const response = await api.post('/api/auth/register', userData);
    if (response.data.access_token) this.saveAuthData(response.data);
    return response.data;
  },

  async registerCustomer(customerData) {
    const response = await api.post('/api/auth/register-customer', customerData);
    if (response.data.access_token) this.saveAuthData(response.data);
    return response.data;
  },

  async login(credentials) {
    const response = await api.post('/api/auth/login', credentials);
    if (response.data.access_token) this.saveAuthData(response.data);
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('karya_token');
    localStorage.removeItem('karya_user');
    window.location.href = '/login';
  },

  saveAuthData(data) {
    localStorage.setItem('karya_token', data.access_token);
    localStorage.setItem('karya_user', JSON.stringify(data.user));
  },

  getToken() {
    return localStorage.getItem('karya_token');
  },

  getUser() {
    const user = localStorage.getItem('karya_user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },
};

export default authService;