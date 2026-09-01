import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Clock, XCircle } from 'lucide-react';
import api from '../api/client';

export default function PaymentCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('checking'); // checking, success, failed

  useEffect(() => {
    const reference = searchParams.get('reference');
    if (!reference) {
      setStatus('failed');
      return;
    }

    api
      .get(`/payments/paystack/verify/${reference}`)
      .then((res) => {
        setStatus(res.data.status === 'success' ? 'success' : 'failed');
      })
      .catch(() => setStatus('failed'));
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center px-5">
      <div className="glass rounded-3xl p-10 text-center max-w-sm w-full fade-in">
        {status === 'checking' && (
          <>
            <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5 animate-pulse" style={{ background: 'rgba(196,181,253,0.15)', color: '#C4B5FD' }}>
              <Clock size={26} />
            </div>
            <h3 className="font-display text-lg font-medium mb-1">Confirming payment...</h3>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
              <Clock size={26} />
            </div>
            <h3 className="font-display text-lg font-medium mb-1">Payment received</h3>
            <p className="text-sm text-[var(--text-3)] mb-6">Pending admin approval before your balance updates.</p>
            <button onClick={() => navigate('/dashboard')} className="btn-primary rounded-full px-6 py-2.5 text-sm font-medium">
              Back to Dashboard
            </button>
          </>
        )}
        {status === 'failed' && (
          <>
            <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}>
              <XCircle size={26} />
            </div>
            <h3 className="font-display text-lg font-medium mb-1">Payment not confirmed</h3>
            <p className="text-sm text-[var(--text-3)] mb-6">If you were charged, contact support — otherwise, try again.</p>
            <button onClick={() => navigate('/deposit')} className="btn-primary rounded-full px-6 py-2.5 text-sm font-medium">
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
}