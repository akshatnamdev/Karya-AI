import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import paymentService from '../services/paymentService';

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const s = document.createElement('script');
    s.src = 'https://checkout.razorpay.com/v1/checkout.js';
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

function PublicPayPage() {
  const { token } = useParams();
  const [session, setSession] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [result, setResult] = useState(null);
  const pollRef = useRef(null);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await paymentService.getPublicSession(token);
      setSession(data);
      if (data.paid || data.status === 'already_paid') {
        setResult({ ok: true, message: data.message || 'Already paid' });
      }
    } catch (e) {
      setError(e.message || 'Unable to load payment link');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) load();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [token]);

  const startPoll = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    let tries = 0;
    pollRef.current = setInterval(async () => {
      tries += 1;
      try {
        const st = await paymentService.getPublicStatus(token);
        if (st.paid || st.link_status === 'paid') {
          clearInterval(pollRef.current);
          setResult({
            ok: true,
            message: 'Payment successful. Invoice updated.',
            ...st,
          });
          setPaying(false);
        }
      } catch (_) {}
      if (tries > 40) {
        clearInterval(pollRef.current);
        setPaying(false);
        setResult({
          ok: false,
          message:
            'Payment submitted. Waiting for confirmation. Refresh in a moment or check with the business.',
        });
      }
    }, 2000);
  };

  const handlePay = async () => {
    setError('');
    setResult(null);
    if (!session || session.status !== 'ready') return;

    setPaying(true);
    const ok = await loadRazorpayScript();
    if (!ok) {
      setError('Could not load Razorpay Checkout');
      setPaying(false);
      return;
    }

    const amountPaise = Math.round(Number(session.amount) * 100);

    const rzp = new window.Razorpay({
      key: session.key_id,
      amount: amountPaise,
      currency: session.currency || 'INR',
      name: 'Karya AI',
      description: `Invoice ${session.invoice_number}`,
      order_id: session.provider_order_id,
      prefill: {
        name: session.customer_name || '',
        email: session.customer_email || '',
        contact: session.customer_phone || '',
      },
      theme: { color: '#111827' },
      handler: async function (response) {
        // NEVER trust UI alone — verify signature on backend
        try {
          const verified = await paymentService.verifyCheckout(token, {
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          setResult({
            ok: true,
            message: verified.message || 'Payment verified',
            ...verified,
          });
          setPaying(false);
        } catch (e) {
          // Checkout succeeded client-side but verify failed — poll webhook path
          setResult({
            ok: false,
            message:
              e.message ||
              'Verifying payment… status will update after gateway confirmation.',
          });
          startPoll();
        }
      },
      modal: {
        ondismiss: function () {
          setPaying(false);
        },
      },
    });

    rzp.on('payment.failed', function (resp) {
      setPaying(false);
      setError(resp?.error?.description || 'Payment failed');
    });

    rzp.open();
  };

  const formatMoney = (n) =>
    `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>Loading payment…</div>
      </div>
    );
  }

  if (error && !session) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <h1 style={styles.title}>Payment unavailable</h1>
          <p style={styles.muted}>{error}</p>
        </div>
      </div>
    );
  }

  const paid =
    result?.ok ||
    session?.paid ||
    session?.status === 'already_paid' ||
    result?.invoice_status === 'paid';

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.brand}>Karya</div>
        <h1 style={styles.title}>Pay invoice</h1>
        <p style={styles.muted}>{session?.invoice_number}</p>

        <div style={styles.row}>
          <span>Amount</span>
          <strong>{formatMoney(session?.amount)}</strong>
        </div>
        {session?.customer_name && (
          <div style={styles.row}>
            <span>Customer</span>
            <span>{session.customer_name}</span>
          </div>
        )}

        {error && <div style={styles.err}>{error}</div>}

        {paid ? (
          <div style={styles.ok}>
            {result?.message || session?.message || 'Payment complete'}
            {result?.invoice_status && (
              <div style={{ marginTop: 8, fontSize: 13 }}>
                Status: {result.invoice_status}
                {result.balance != null ? ` · Balance ${formatMoney(result.balance)}` : ''}
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            style={styles.btn}
            disabled={paying || session?.status !== 'ready'}
            onClick={handlePay}
          >
            {paying ? 'Processing…' : `Pay ${formatMoney(session?.amount)}`}
          </button>
        )}

        {!paid && result?.message && !result?.ok && (
          <p style={{ ...styles.muted, marginTop: 12 }}>{result.message}</p>
        )}

        <p style={{ ...styles.muted, marginTop: 20, fontSize: 11 }}>
          Payment is confirmed only after gateway verification. Closing the window
          does not mark the invoice paid by itself.
        </p>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#f3f4f6',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    fontFamily: 'system-ui, sans-serif',
  },
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: 28,
    width: '100%',
    maxWidth: 420,
    boxShadow: '0 10px 30px rgba(0,0,0,0.08)',
  },
  brand: { fontWeight: 700, fontSize: 14, color: '#111827', marginBottom: 8 },
  title: { margin: '0 0 4px', fontSize: 22, color: '#111827' },
  muted: { color: '#6b7280', fontSize: 13, margin: '0 0 16px' },
  row: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: '1px solid #f3f4f6',
    fontSize: 14,
    color: '#374151',
  },
  btn: {
    marginTop: 20,
    width: '100%',
    background: '#111827',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '12px 16px',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
  },
  err: {
    marginTop: 12,
    background: '#fef2f2',
    color: '#991b1b',
    padding: 10,
    borderRadius: 8,
    fontSize: 13,
  },
  ok: {
    marginTop: 16,
    background: '#ecfdf5',
    color: '#065f46',
    padding: 14,
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 500,
  },
};

export default PublicPayPage;