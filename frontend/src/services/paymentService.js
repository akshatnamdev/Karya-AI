import api from './api';

const BASE = api.defaults.baseURL || 'http://localhost:8000';

export const paymentService = {
  async getStatus() {
    const res = await api.get('/api/payments/status');
    return res.data;
  },

  async createPaymentLink(invoiceId) {
    const res = await api.post(`/api/invoices/${invoiceId}/payment-link`);
    return res.data;
    },

  async createLink(invoiceId) {
    const res = await api.post(`/api/invoices/${invoiceId}/payment-link`);
    return res.data;
  },

  // Public (no JWT) — use plain fetch so interceptors don't force login
  async getPublicSession(token) {
    const res = await fetch(`${BASE}/api/public/pay/${token}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Failed to load payment');
    return data;
  },

  async getPublicStatus(token) {
    const res = await fetch(`${BASE}/api/public/pay/${token}/status`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Failed to get status');
    return data;
  },

  async verifyCheckout(token, payload) {
    // payload: { razorpay_order_id, razorpay_payment_id, razorpay_signature }
    const res = await fetch(`${BASE}/api/public/pay/${token}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Verification failed');
    return data;
  },
};

export default paymentService;