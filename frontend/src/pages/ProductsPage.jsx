import { useState, useEffect, useMemo } from 'react';
import Layout from '../components/Layout';
import productService from '../services/productService';
import { Loader2 } from 'lucide-react';
import '../styles/DataPage.css';
import { useAuth } from '../context/AuthContext'; // adjust path if your file is contexts/AuthContext.jsx
import AddProductModal from '../components/AddProductModal';
import { Plus } from 'lucide-react';

function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const { isBusinessOwner } = useAuth();
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [stockMode, setStockMode] = useState('add'); // set | add | remove
  const [stockQty, setStockQty] = useState('');
  const [stockSaving, setStockSaving] = useState(false);
  const [stockError, setStockError] = useState('');
  const [stockSuccess, setStockSuccess] = useState('');

  useEffect(() => {
    loadProducts();
  }, []);

  const handleStockUpdate = async () => {
    if (!selected || !isBusinessOwner) return;
    setStockError('');
    setStockSuccess('');

    const qty = parseInt(stockQty, 10);
    if (Number.isNaN(qty) || qty < 0) {
      setStockError('Enter a valid quantity');
      return;
    }

    try {
      setStockSaving(true);
      const updated = await productService.updateStock(selected.id, {
        mode: stockMode,
        quantity: qty,
        reason: 'manual_ui',
      });
      setStockSuccess('Stock updated');
      setStockQty('');
      // refresh list + selected
      await loadProducts();
      setSelected(updated);
    } catch (err) {
      setStockError(
        err.response?.data?.detail || err.message || 'Failed to update stock'
      );
    } finally {
      setStockSaving(false);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await productService.getAll();
      setProducts(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load products');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = useMemo(() => {
    let list = products;

    if (filter === 'low') {
      list = list.filter((p) => p.needs_reorder);
    } else if (filter === 'critical') {
      list = list.filter(
        (p) => p.needs_reorder && p.stock < (p.reorder_level || 0) * 0.5
      );
    } else if (filter === 'ok') {
      list = list.filter((p) => !p.needs_reorder);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.sku?.toLowerCase().includes(q) ||
          p.category?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [products, search, filter]);

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  const stockStatus = (p) => {
    const stock = p.stock || 0;
    const reorder = p.reorder_level || 0;
    if (stock < reorder * 0.5) return { dot: 'red', label: 'Critical' };
    if (stock <= reorder) return { dot: 'amber', label: 'Low' };
    return { dot: 'green', label: 'OK' };
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading-box">
          <Loader2 size={20} className="spin" />
        </div>
      </Layout>
    );
  }

  const lowCount = products.filter((p) => p.needs_reorder).length;

  return (
    <Layout>
      <header className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <h1 className="page-title">Inventory</h1>
          <p className="page-subtitle">
            {products.length} products · {lowCount} need reordering
          </p>
        </div>
        {isBusinessOwner && (
          <button
            type="button"
            onClick={() => setShowAddProduct(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: '#111827',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            <Plus size={16} />
            Add Product
          </button>
          
        )}
      </header>

      {error && (
        <div style={{ color: '#991b1b', marginBottom: 16, fontSize: 13 }}>{error}</div>
      )}

      <div className="page-toolbar">
        <input
          className="search-input"
          placeholder="Search product, SKU, category..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          <button
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-tab ${filter === 'critical' ? 'active' : ''}`}
            onClick={() => setFilter('critical')}
          >
            Critical
          </button>
          <button
            className={`filter-tab ${filter === 'low' ? 'active' : ''}`}
            onClick={() => setFilter('low')}
          >
            Low
          </button>
          <button
            className={`filter-tab ${filter === 'ok' ? 'active' : ''}`}
            onClick={() => setFilter('ok')}
          >
            Healthy
          </button>
        </div>
      </div>

      <div className="detail-layout">
        <div className="data-table-wrap">
          {filtered.length === 0 ? (
            <div className="empty-state-box">No products found</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Category</th>
                  <th className="right">Stock</th>
                  <th className="right">Price</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => {
                  const status = stockStatus(p);
                  return (
                    <tr
                      key={p.id}
                      className={selected?.id === p.id ? 'selected' : ''}
                      onClick={() => setSelected(p)}
                    >
                      <td className="cell-primary">{p.name}</td>
                      <td className="cell-mono">{p.sku || '—'}</td>
                      <td className="cell-muted">{p.category || '—'}</td>
                      <td className="right">
                        <span className="cell-primary">{p.stock ?? 0}</span>
                        <span className="cell-muted"> / {p.reorder_level ?? 0}</span>
                      </td>
                      <td className="right cell-primary">{formatMoney(p.selling_price)}</td>
                      <td>
                        <span className="status-pill">
                          <span className={`status-dot ${status.dot}`} />
                          {status.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            
          )}
        </div>

        <aside className="detail-panel">
          {!selected ? (
            <div className="detail-empty">Select a product to view details</div>
          ) : (
            <>
              <div className="detail-panel-title">{selected.name}</div>

              <div className="detail-row">
                <span className="detail-label">SKU</span>
                <span className="detail-value">{selected.sku || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Category</span>
                <span className="detail-value">{selected.category || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Unit</span>
                <span className="detail-value">{selected.unit || '—'}</span>
              </div>

              <div className="detail-section-label">Pricing</div>
              <div className="detail-row">
                <span className="detail-label">Cost</span>
                <span className="detail-value">{formatMoney(selected.cost_price)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Selling</span>
                <span className="detail-value">{formatMoney(selected.selling_price)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">MRP</span>
                <span className="detail-value">{formatMoney(selected.mrp)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">GST</span>
                <span className="detail-value">{selected.gst_rate ?? 0}%</span>
              </div>

              <div className="detail-section-label">Stock</div>
              <div className="detail-row">
                <span className="detail-label">Current</span>
                <span className="detail-value">{selected.stock ?? 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Reorder at</span>
                <span className="detail-value">{selected.reorder_level ?? 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Reorder qty</span>
                <span className="detail-value">{selected.reorder_quantity ?? 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Location</span>
                <span className="detail-value">{selected.warehouse_location || '—'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status</span>
                <span className="detail-value">
                  <span className="status-pill">
                    <span className={`status-dot ${stockStatus(selected).dot}`} />
                    {stockStatus(selected).label}
                  </span>
                </span>
                
              </div>
                            {isBusinessOwner && (
                <>
                  <div className="detail-section-label">Update stock</div>
                  {stockError && (
                    <div style={{ color: '#991b1b', fontSize: 12, marginBottom: 8 }}>
                      {String(stockError)}
                    </div>
                  )}
                  {stockSuccess && (
                    <div style={{ color: '#166534', fontSize: 12, marginBottom: 8 }}>
                      {stockSuccess}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                    <select
                      className="search-input"
                      style={{ width: 120 }}
                      value={stockMode}
                      onChange={(e) => setStockMode(e.target.value)}
                    >
                      <option value="add">Add</option>
                      <option value="remove">Remove</option>
                      <option value="set">Set exact</option>
                    </select>
                    <input
                      className="search-input"
                      style={{ width: 100 }}
                      type="number"
                      min="0"
                      placeholder="Qty"
                      value={stockQty}
                      onChange={(e) => setStockQty(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={handleStockUpdate}
                      disabled={stockSaving}
                      style={{
                        background: '#111827',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 8,
                        padding: '8px 12px',
                        fontSize: 13,
                        cursor: 'pointer',
                      }}
                    >
                      {stockSaving ? 'Saving…' : 'Update'}
                    </button>
                  </div>
                </>
              )}

              {selected.description && (
                <>
                  <div className="detail-section-label">Description</div>
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
                    {selected.description}
                  </div>
                </>
              )}
            </>
          )}
        </aside>
      </div>
            {isBusinessOwner && (
        <AddProductModal
          open={showAddProduct}
          onClose={() => setShowAddProduct(false)}
          onCreated={() => {
            loadProducts();
          }}
        />
      )}
    </Layout>
  );
}

export default ProductsPage;