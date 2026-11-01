import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { page } from './utils/lazyPage';
import PageLoader from './components/PageLoader';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import AppLayout from './layouts/AppLayout';
import AdminLayout from './layouts/AdminLayout';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
const Dashboard = page('/dashboard', () => import('./pages/Dashboard'));
const Transfer = page('/transfer', () => import('./pages/Transfer'));
const Deposit = page('/deposit', () => import('./pages/Deposit'));
const Withdraw = page('/withdraw', () => import('./pages/Withdraw'));
const History = page('/history', () => import('./pages/History'));
const Profile = page('/profile', () => import('./pages/Profile'));
const Beneficiaries = page('/beneficiaries', () => import('./pages/Beneficiaries'));
const Receive = page('/receive', () => import('./pages/Receive'));
const Loans = page('/loans', () => import('./pages/Loans'));
const FixedDeposits = page('/fixed-deposits', () => import('./pages/FixedDeposits'));
const Cards = page('/cards', () => import('./pages/Cards'));
const Kyc = page('/kyc', () => import('./pages/Kyc'));
const PaymentCallback = page('/payment-callback', () => import('./pages/PaymentCallback'));
const BtcWallet = page('/btc-wallet', () => import('./pages/BtcWallet'));
const BankAccount = page('/bank-account', () => import('./pages/BankAccount'));
const Settings = page('/settings', () => import('./pages/Settings'));
const Statements = page('/statements', () => import('./pages/Statements'));
const Receipt = page('/receipt/:id', () => import('./pages/Receipt'));
const SavedPayments = page('/saved-payments', () => import('./pages/SavedPayments'));
const Contact = page('/contact', () => import('./pages/Contact'));
const Save4Me = page('/save4me', () => import('./pages/Save4Me'));
const ScheduledTransfers = page('/scheduled', () => import('./pages/ScheduledTransfers'));
const Referrals = page('/referrals', () => import('./pages/Referrals'));

const AdminPending = page('/admin/pending', () => import('./pages/admin/AdminPending'));
const AdminUsers = page('/admin/users', () => import('./pages/admin/AdminUsers'));
const AdminTransactions = page('/admin/transactions', () => import('./pages/admin/AdminTransactions'));
const AdminTransactionDetail = page('/admin/transactions/:id', () => import('./pages/admin/AdminTransactionDetail'));
const AdminLoans = page('/admin/loans', () => import('./pages/admin/AdminLoans'));
const AdminCards = page('/admin/cards', () => import('./pages/admin/AdminCards'));
const AdminKyc = page('/admin/kyc', () => import('./pages/admin/AdminKyc'));
const AdminFlagged = page('/admin/flagged', () => import('./pages/admin/AdminFlagged'));
const AdminWalletApplications = page('/admin/wallet-applications', () => import('./pages/admin/AdminWalletApplications'));
const AdminSupport = page('/admin/support', () => import('./pages/admin/AdminSupport'));

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/payment-callback" element={<PaymentCallback />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transfer" element={<Transfer />} />
          <Route path="/deposit" element={<Deposit />} />
          <Route path="/withdraw" element={<Withdraw />} />
          <Route path="/history" element={<History />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/beneficiaries" element={<Beneficiaries />} />
          <Route path="/receive" element={<Receive />} />
          <Route path="/loans" element={<Loans />} />
          <Route path="/fixed-deposits" element={<FixedDeposits />} />
          <Route path="/cards" element={<Cards />} />
          <Route path="/kyc" element={<Kyc />} />
          <Route path="/btc-wallet" element={<BtcWallet />} />
          <Route path="/bank-account" element={<BankAccount />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/statements" element={<Statements />} />
          <Route path="/receipt/:id" element={<Receipt />} />
          <Route path="/saved-payments" element={<SavedPayments />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/save4me" element={<Save4Me />} />
          <Route path="/scheduled" element={<ScheduledTransfers />} />
          <Route path="/referrals" element={<Referrals />} />
        </Route>

        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<Navigate to="/admin/pending" replace />} />
            <Route path="/admin/pending" element={<AdminPending />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/transactions" element={<AdminTransactions />} />
            <Route path="/admin/transactions/:id" element={<AdminTransactionDetail />} />
            <Route path="/admin/loans" element={<AdminLoans />} />
            <Route path="/admin/cards" element={<AdminCards />} />
            <Route path="/admin/kyc" element={<AdminKyc />} />
            <Route path="/admin/flagged" element={<AdminFlagged />} />
            <Route path="/admin/wallet-applications" element={<AdminWalletApplications />} />
            <Route path="/admin/support" element={<AdminSupport />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
    </Suspense>
  );
}

export default App;