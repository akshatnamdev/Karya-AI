import api from './api';

export const adminService = {
  stats: () => api.get('/api/admin/stats').then(r => r.data),
  listBusinesses: () => api.get('/api/admin/businesses').then(r => r.data),
  businessDetail: (id) => api.get(`/api/admin/businesses/${id}`).then(r => r.data),
  deleteBusiness: (id) => api.delete(`/api/admin/businesses/${id}`).then(r => r.data),
  setBusinessActive: (id, active) =>
    api.patch(`/api/admin/businesses/${id}/active?active=${active}`).then(r => r.data),
  listUsers: () => api.get('/api/admin/users').then(r => r.data),
  setUserActive: (id, active) =>
    api.patch(`/api/admin/users/${id}/active?active=${active}`).then(r => r.data),
};

export default adminService;