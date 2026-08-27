import api from './api';

export const orderService = {
  async getAll() {
    const response = await api.get('/api/orders');
    return response.data;
  },

  async getById(id) {
    const response = await api.get(`/api/orders/${id}`);
    return response.data;
  },

  async getWhatsappOrders() {
    const response = await api.get('/api/orders/whatsapp');
    return response.data;
  },

  async create(payload) {
    const response = await api.post('/api/orders', payload);
    return response.data;
  },
};

export default orderService;