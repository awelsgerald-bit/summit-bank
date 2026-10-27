import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import AppLayout from './layouts/AppLayout';
import AdminLayout from './layouts/AdminLayout';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Transfer from './pages/Transfer';
import Deposit from './pages/Deposit';
import Withdraw from './pages/Withdraw';
import History from './pages/History';
import Profile from './pages/Profile';
import Beneficiaries from './pages/Beneficiaries';
import Receive from './pages/Receive';
import Loans from './pages/Loans';
import FixedDeposits from './pages/FixedDeposits';
import Cards from './pages/Cards';
import Kyc from './pages/Kyc';
import PaymentCallback from './pages/PaymentCallback';
import BtcWallet from './pages/BtcWallet';
import BankAccount from './pages/BankAccount';
import Settings from './pages/Settings';
import Statements from './pages/Statements';
import Receipt from './pages/Receipt';
import SavedPayments from './pages/SavedPayments';
import Contact from './pages/Contact';
import Save4Me from './pages/Save4Me';

import AdminPending from './pages/admin/AdminPending';
import AdminUsers from './pages/admin/AdminUsers';
import AdminTransactions from './pages/admin/AdminTransactions';
import AdminTransactionDetail from './pages/admin/AdminTransactionDetail';
import AdminLoans from './pages/admin/AdminLoans';
import AdminCards from './pages/admin/AdminCards';
import AdminKyc from './pages/admin/AdminKyc';
import AdminFlagged from './pages/admin/AdminFlagged';
import AdminWalletApplications from './pages/admin/AdminWalletApplications';
import AdminSupport from './pages/admin/AdminSupport';

function App() {
  return (
    <Routes>
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
  );
}

export default App;