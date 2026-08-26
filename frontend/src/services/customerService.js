import api from './api';

export const customerService = {
  async getAll() {
    const response = await api.get('/api/customers');
    return response.data;
  },

  async getById(id) {
    const response = await api.get(`/api/customers/${id}`);
    return response.data;
  },
};

export default customerService;