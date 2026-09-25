import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('karya_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Attach active business ID for multi-business customers
    const activeBusinessId = localStorage.getItem('karya_active_business_id');
    if (activeBusinessId) {
      config.headers['X-Business-Id'] = activeBusinessId;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('karya_token');
      localStorage.removeItem('karya_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;