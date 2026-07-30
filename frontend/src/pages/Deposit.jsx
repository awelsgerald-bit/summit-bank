import AmountActionForm from '../components/AmountActionForm';

export default function Deposit() {
  return (
    <AmountActionForm
      mode="deposit"
      title="Deposit Funds"
      endpoint="/transactions/deposit"
      buttonLabel="Add Fund"
    />
  );
}