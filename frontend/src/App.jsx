import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PageLoading from './components/PageLoading';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import AppLayout from './layouts/AppLayout';
import AdminLayout from './layouts/AdminLayout';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Transfer = lazy(() => import('./pages/Transfer'));
const Deposit = lazy(() => import('./pages/Deposit'));
const Withdraw = lazy(() => import('./pages/Withdraw'));
const History = lazy(() => import('./pages/History'));
const Profile = lazy(() => import('./pages/Profile'));
const Beneficiaries = lazy(() => import('./pages/Beneficiaries'));
const Receive = lazy(() => import('./pages/Receive'));
const Loans = lazy(() => import('./pages/Loans'));
const FixedDeposits = lazy(() => import('./pages/FixedDeposits'));
const Cards = lazy(() => import('./pages/Cards'));
const Kyc = lazy(() => import('./pages/Kyc'));
const PaymentCallback = lazy(() => import('./pages/PaymentCallback'));
const BtcWallet = lazy(() => import('./pages/BtcWallet'));
const BankAccount = lazy(() => import('./pages/BankAccount'));
const Settings = lazy(() => import('./pages/Settings'));
const Statements = lazy(() => import('./pages/Statements'));
const Receipt = lazy(() => import('./pages/Receipt'));
const SavedPayments = lazy(() => import('./pages/SavedPayments'));
const Contact = lazy(() => import('./pages/Contact'));
const Save4Me = lazy(() => import('./pages/Save4Me'));
const ScheduledTransfers = lazy(() => import('./pages/ScheduledTransfers'));
const Referrals = lazy(() => import('./pages/Referrals'));

const AdminPending = lazy(() => import('./pages/admin/AdminPending'));
const AdminUsers = lazy(() => import('./pages/admin/AdminUsers'));
const AdminTransactions = lazy(() => import('./pages/admin/AdminTransactions'));
const AdminTransactionDetail = lazy(() => import('./pages/admin/AdminTransactionDetail'));
const AdminLoans = lazy(() => import('./pages/admin/AdminLoans'));
const AdminCards = lazy(() => import('./pages/admin/AdminCards'));
const AdminKyc = lazy(() => import('./pages/admin/AdminKyc'));
const AdminFlagged = lazy(() => import('./pages/admin/AdminFlagged'));
const AdminWalletApplications = lazy(() => import('./pages/admin/AdminWalletApplications'));
const AdminSupport = lazy(() => import('./pages/admin/AdminSupport'));

function App() {
  return (
    <Suspense fallback={<PageLoading />}>
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