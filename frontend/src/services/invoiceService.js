import api from './api';

export const invoiceService = {
  async getAll() {
    const response = await api.get('/api/invoices');
    return response.data;
  },

  async getById(id) {
    const response = await api.get(`/api/invoices/${id}`);
    return response.data;
  },

  async getOverdue() {
    const response = await api.get('/api/invoices/overdue');
    return response.data;
  },

  // NEW — Razorpay-ready
  async recordPayment(invoiceId, payload) {
    // payload: { amount, payment_method?: 'manual'|'cash'|'upi'|'razorpay', note?, reference? }
    const response = await api.post(`/api/invoices/${invoiceId}/payments`, payload);
    return response.data;
  },
};

export default invoiceService;