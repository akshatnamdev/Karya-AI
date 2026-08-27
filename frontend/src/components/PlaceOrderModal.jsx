import { useEffect, useState } from 'react';
import { Loader2, Plus, Trash2, X } from 'lucide-react';
import orderService from '../services/orderService';
import productService from '../services/productService';
import customerService from '../services/customerService';

function PlaceOrderModal({ open, onClose, onCreated, mode }) {
  // mode: 'business' | 'customer'
  const isBusiness = mode === 'business';

  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState([{ product_id: '', quantity: 1 }]);
  const [loadingMeta, setLoadingMeta] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    const load = async () => {
      setLoadingMeta(true);
      setError('');
      try {
        const prodData = await productService.getAll();
        if (cancelled) return;
        setProducts(Array.isArray(prodData) ? prodData : prodData?.products || []);

        if (isBusiness) {
          try {
            const custData = await customerService.getAll();
            if (cancelled) return;
            // support array or { customers: [] }
            const list = Array.isArray(custData)
              ? custData
              : custData?.customers || custData?.data || [];
            setCustomers(list);
          } catch (e) {
            console.error(e);
            setError('Could not load customers list');
          }
        }
      } catch (e) {
        console.error(e);
        setError('Could not load products');
      } finally {
        if (!cancelled) setLoadingMeta(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [open, isBusiness]);

  if (!open) return null;

  const updateItem = (index, key, value) => {
    setItems((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [key]: value } : row))
    );
  };

  const addRow = () => setItems((prev) => [...prev, { product_id: '', quantity: 1 }]);

  const removeRow = (index) => {
    setItems((prev) => (prev.length === 1 ? prev : prev.filter((_, i) => i !== index)));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (isBusiness && !customerId) {
      setError('Please select a customer');
      return;
    }

    const cleaned = items
      .map((row) => ({
        product_id: Number(row.product_id),
        quantity: parseInt(row.quantity, 10),
      }))
      .filter((row) => row.product_id && row.quantity > 0);

    if (!cleaned.length) {
      setError('Add at least one product with quantity > 0');
      return;
    }

    const payload = {
      items: cleaned,
      notes: notes.trim() || null,
      source: 'manual',
    };
    if (isBusiness) {
      payload.customer_id = Number(customerId);
    }

    try {
      setSaving(true);
      const created = await orderService.create(payload);
      setCustomerId('');
      setNotes('');
      setItems([{ product_id: '', quantity: 1 }]);
      onCreated?.(created);
      onClose?.();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : err.message || 'Failed to place order'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h2 style={styles.title}>{isBusiness ? 'Create Order' : 'Place Order'}</h2>
          <button type="button" style={styles.iconBtn} onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {loadingMeta ? (
          <div style={{ padding: 24, display: 'flex', justifyContent: 'center' }}>
            <Loader2 size={20} className="spin" />
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && <div style={styles.error}>{String(error)}</div>}

            {isBusiness && (
              <label style={styles.label}>
                Customer *
                <select
                  style={styles.input}
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  required
                >
                  <option value="">Select customer…</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name || c.customer_name || `Customer #${c.id}`}
                      {c.phone ? ` · ${c.phone}` : ''}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <div style={{ marginTop: 14, marginBottom: 6, fontSize: 12, fontWeight: 600, color: '#374151' }}>
              Items
            </div>

            {items.map((row, index) => (
              <div key={index} style={styles.itemRow}>
                <select
                  style={{ ...styles.input, flex: 1 }}
                  value={row.product_id}
                  onChange={(e) => updateItem(index, 'product_id', e.target.value)}
                  required
                >
                  <option value="">Select product…</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} · ₹{p.selling_price}
                      {p.stock != null ? ` · stock ${p.stock}` : ''}
                    </option>
                  ))}
                </select>
                <input
                  style={{ ...styles.input, width: 88 }}
                  type="number"
                  min="1"
                  value={row.quantity}
                  onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                  required
                />
                <button
                  type="button"
                  style={styles.iconBtn}
                  onClick={() => removeRow(index)}
                  disabled={items.length === 1}
                  title="Remove"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}

            <button type="button" style={styles.addRowBtn} onClick={addRow}>
              <Plus size={14} /> Add item
            </button>

            <label style={{ ...styles.label, marginTop: 14 }}>
              Notes
              <textarea
                style={{ ...styles.input, minHeight: 64, resize: 'vertical' }}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional"
              />
            </label>

            <div style={styles.footer}>
              <button type="button" style={styles.btnSecondary} onClick={onClose} disabled={saving}>
                Cancel
              </button>
              <button type="submit" style={styles.btnPrimary} disabled={saving}>
                {saving ? <Loader2 size={16} className="spin" /> : null}
                {saving ? ' Placing…' : isBusiness ? 'Create order' : 'Place order'}
              </button>
            </div>
          </form>
        )}
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
    background: '#fff',
  },
  itemRow: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  addRowBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    border: '1px dashed #d1d5db',
    background: '#f9fafb',
    borderRadius: 8,
    padding: '6px 10px',
    fontSize: 12,
    color: '#374151',
    cursor: 'pointer',
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

export default PlaceOrderModal;