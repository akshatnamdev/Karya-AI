import { useState } from 'react';
import { Loader2, X } from 'lucide-react';
import productService from '../services/productService';

const empty = {
  name: '',
  sku: '',
  category: '',
  description: '',
  selling_price: '',
  cost_price: '',
  mrp: '',
  unit: 'pcs',
  initial_stock: '0',
  reorder_level: '10',
  reorder_quantity: '50',
};

function AddProductModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  if (!open) return null;

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.name.trim()) {
      setError('Product name is required');
      return;
    }
    const price = Number(form.selling_price);
    if (Number.isNaN(price) || price < 0) {
      setError('Valid selling price is required');
      return;
    }

    const payload = {
      name: form.name.trim(),
      sku: form.sku.trim() || null,
      category: form.category.trim() || null,
      description: form.description.trim() || null,
      selling_price: price,
      cost_price: form.cost_price === '' ? 0 : Number(form.cost_price),
      mrp: form.mrp === '' ? null : Number(form.mrp),
      unit: form.unit || 'pcs',
      initial_stock: parseInt(form.initial_stock || '0', 10),
      reorder_level: parseInt(form.reorder_level || '10', 10),
      reorder_quantity: parseInt(form.reorder_quantity || '50', 10),
    };

    try {
      setSaving(true);
      const created = await productService.create(payload);
      setForm(empty);
      onCreated?.(created);
      onClose?.();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to create product'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h2 style={styles.title}>Add Product</h2>
          <button type="button" style={styles.iconBtn} onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div style={styles.error}>{String(error)}</div>}

          <div style={styles.grid}>
            <label style={styles.label}>
              Name *
              <input style={styles.input} value={form.name} onChange={set('name')} required />
            </label>
            <label style={styles.label}>
              Selling price (₹) *
              <input
                style={styles.input}
                type="number"
                min="0"
                step="0.01"
                value={form.selling_price}
                onChange={set('selling_price')}
                required
              />
            </label>
            <label style={styles.label}>
              SKU
              <input style={styles.input} value={form.sku} onChange={set('sku')} />
            </label>
            <label style={styles.label}>
              Category
              <input style={styles.input} value={form.category} onChange={set('category')} />
            </label>
            <label style={styles.label}>
              Unit
              <input style={styles.input} value={form.unit} onChange={set('unit')} placeholder="pcs" />
            </label>
            <label style={styles.label}>
              Cost price (₹)
              <input
                style={styles.input}
                type="number"
                min="0"
                step="0.01"
                value={form.cost_price}
                onChange={set('cost_price')}
              />
            </label>
            <label style={styles.label}>
              MRP (₹)
              <input
                style={styles.input}
                type="number"
                min="0"
                step="0.01"
                value={form.mrp}
                onChange={set('mrp')}
              />
            </label>
            <label style={styles.label}>
              Initial stock
              <input
                style={styles.input}
                type="number"
                min="0"
                value={form.initial_stock}
                onChange={set('initial_stock')}
              />
            </label>
            <label style={styles.label}>
              Reorder level
              <input
                style={styles.input}
                type="number"
                min="0"
                value={form.reorder_level}
                onChange={set('reorder_level')}
              />
            </label>
            <label style={styles.label}>
              Reorder qty
              <input
                style={styles.input}
                type="number"
                min="0"
                value={form.reorder_quantity}
                onChange={set('reorder_quantity')}
              />
            </label>
          </div>

          <label style={{ ...styles.label, marginTop: 12 }}>
            Description
            <textarea
              style={{ ...styles.input, minHeight: 72, resize: 'vertical' }}
              value={form.description}
              onChange={set('description')}
            />
          </label>

          <div style={styles.footer}>
            <button type="button" style={styles.btnSecondary} onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" style={styles.btnPrimary} disabled={saving}>
              {saving ? <Loader2 size={16} className="spin" /> : null}
              {saving ? ' Saving…' : 'Save product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(15,23,42,0.45)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: 16,
  },
  modal: {
    background: '#fff',
    borderRadius: 12,
    width: '100%',
    maxWidth: 560,
    maxHeight: '90vh',
    overflow: 'auto',
    padding: 20,
    boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: { margin: 0, fontSize: 18, fontWeight: 600, color: '#111827' },
  iconBtn: {
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    padding: 4,
    color: '#6b7280',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 12,
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    fontSize: 12,
    fontWeight: 500,
    color: '#374151',
  },
  input: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '8px 10px',
    fontSize: 14,
    color: '#111827',
    outline: 'none',
  },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 20,
  },
  btnPrimary: {
    background: '#111827',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '8px 14px',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
  },
  btnSecondary: {
    background: '#fff',
    color: '#374151',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '8px 14px',
    fontSize: 13,
    cursor: 'pointer',
  },
  error: {
    background: '#fef2f2',
    color: '#991b1b',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: '8px 10px',
    fontSize: 13,
    marginBottom: 12,
  },
};

export default AddProductModal;