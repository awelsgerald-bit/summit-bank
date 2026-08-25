import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Clock, QrCode } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import BankCard from '../components/BankCard';
import QrScannerModal from '../components/QrScannerModal';

export default function Transfer() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [recipientAccount, setRecipientAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Beneficiaries
  const [beneficiaries, setBeneficiaries] = useState([]);

  // QR Scanner
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scannedName, setScannedName] = useState('');

  useEffect(() => {
    api
      .get('/beneficiaries')
      .then((res) => setBeneficiaries(res.data))
      .catch(() => {});
  }, []);

  function handleScan(decodedText, scanError) {
    setScannerOpen(false);

    if (scanError) {
      setError(scanError);
      return;
    }

    try {
      const data = JSON.parse(decodedText);

      if (
        data.type === 'summit_bank_account' &&
        data.account_number
      ) {
        setRecipientAccount(data.account_number);
        setScannedName(data.name || '');
        setError('');
      } else {
        setError(
          "That QR code isn't a valid Summit Bank account code."
        );
      }
    } catch {
      setError('Could not read that QR code.');
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const numericAmount = parseFloat(amount);

    if (!numericAmount || numericAmount <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }

    if (!recipientAccount.trim()) {
      setError('Enter a recipient account number.');
      return;
    }

    setSubmitting(true);

    try {
      await api.post('/transactions/transfer', {
        recipient_account_number: recipientAccount.trim(),
        amount: numericAmount,
        description: description || undefined,
      });

      // Show pending approval screen.
      // No automatic redirect so the user has time to save the beneficiary.
      setSuccess(true);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          'Transfer failed. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    const alreadySaved = beneficiaries.some(
      (b) => b.account_number === recipientAccount
    );

    return (
      <div className="max-w-lg mx-auto fade-in space-y-4">
        <div className="glass rounded-3xl p-10 text-center">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5"
            style={{
              background: 'rgba(251,191,36,0.15)',
              color: '#FBBF24',
            }}
          >
            <Clock size={26} />
          </div>

          <h3 className="font-display text-lg font-medium mb-1">
            Transfer submitted
          </h3>

          <p className="text-sm text-[var(--text-3)]">
            Pending admin approval. Funds will move once it's reviewed.
          </p>
        </div>

        {!alreadySaved && (
          <button
            onClick={async () => {
              try {
                await api.post('/beneficiaries', {
                  nickname: recipientAccount,
                  account_number: recipientAccount,
                });
              } catch {
                // Saving the beneficiary is optional.
              }

              navigate('/dashboard');
            }}
            className="ghost-btn w-full rounded-2xl py-2.5 text-xs"
          >
            Save {recipientAccount} as a beneficiary
          </button>
        )}

        {alreadySaved && (
          <button
            onClick={() => navigate('/dashboard')}
            className="ghost-btn w-full rounded-2xl py-2.5 text-xs"
          >
            Back to dashboard
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">

      {/* QR Scanner Modal */}
      {scannerOpen && (
        <QrScannerModal
          onScan={handleScan}
          onClose={() => setScannerOpen(false)}
        />
      )}

      <div className="flex items-center gap-3 mb-1">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-[var(--text-2)]"
        >
          <ChevronLeft size={20} />
        </button>

        <h3 className="font-display text-lg font-medium">
          Send Money
        </h3>
      </div>

      <p className="text-sm text-[var(--text-3)] -mt-4">
        Transfers arrive instantly between Summit Bank accounts.
      </p>

      <BankCard
        accountNumber={user?.account_number}
        cardHolder={user?.full_name}
        balance={Number(user?.balance ?? 0)}
        createdAt={user?.created_at}
      />

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">

        {/* Scan QR */}
        <button
          type="button"
          onClick={() => setScannerOpen(true)}
          className="ghost-btn w-full rounded-2xl py-2.5 text-xs flex items-center justify-center gap-2"
        >
          <QrCode size={14} />
          Scan QR to fill recipient
        </button>

        {/* Beneficiary Picker */}
        {beneficiaries.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-1">
            {beneficiaries.map((b) => (
              <button
                key={b.id}
                type="button"
                onClick={() => {
                  setRecipientAccount(b.account_number);
                  setScannedName('');
                }}
                className="toggle-pill rounded-full px-3 py-1.5 text-xs whitespace-nowrap text-[var(--text-2)] hover:text-[var(--text-1)] shrink-0"
              >
                {b.nickname}
              </button>
            ))}
          </div>
        )}

        {/* Account Number */}
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">
            Account Number
          </label>

          <div className="input-field rounded-xl px-4 py-3">
            <input
              required
              value={recipientAccount}
              onChange={(e) => {
                setRecipientAccount(e.target.value);
                setScannedName('');
              }}
              placeholder="0000000000"
              className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>

        {/* Scanned Name */}
        {scannedName && (
          <p
            className="text-xs -mt-2"
            style={{ color: 'var(--pink-accent)' }}
          >
            Scanned: {scannedName}
          </p>
        )}

        {/* Amount */}
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">
            Enter Amount
          </label>

          <div className="input-field rounded-xl px-4 py-3 flex items-center gap-1">
            <span className="text-[var(--text-3)]">$</span>

            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">
            Description (optional)
          </label>

          <div className="input-field rounded-xl px-4 py-3">
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this for?"
              className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>

        {/* Balance + Submit */}
        <div className="flex items-center justify-between pt-2">
          <div>
            <p className="text-[10px] text-[var(--text-3)] uppercase tracking-wide">
              Available Balance
            </p>

            <p className="font-display text-lg font-semibold">
              $
              {Number(user?.balance ?? 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </p>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="btn-primary rounded-full px-8 py-3 text-sm font-medium"
          >
            {submitting ? 'Sending...' : 'Send Money'}
          </button>
        </div>
      </form>
    </div>
  );
}