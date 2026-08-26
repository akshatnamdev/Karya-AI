import api from './api';

export const invoiceService = {
  async getAll() {
    const response = await api.get('/api/invoices');
    return response.data;
  },

  async getOverdue() {
    const response = await api.get('/api/invoices/overdue');
    return response.data;
  },

  async getById(id) {
    const response = await api.get(`/api/invoices/${id}`);
    return response.data;
  },
};

export default invoiceService;