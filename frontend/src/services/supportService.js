import api from './api';

export const supportService = {
  list: () => api.get('/api/support/tickets').then(r => r.data),
  create: (subject, body) =>
    api.post('/api/support/tickets', { subject, body }).then(r => r.data),
  get: (id) => api.get(`/api/support/tickets/${id}`).then(r => r.data),
  reply: (id, body) =>
    api.post(`/api/support/tickets/${id}/reply`, { body }).then(r => r.data),
  escalate: (id) => api.post(`/api/support/tickets/${id}/escalate`).then(r => r.data),
  resolve: (id) => api.post(`/api/support/tickets/${id}/resolve`).then(r => r.data),
};

export default supportService;