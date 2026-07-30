import AmountActionForm from '../components/AmountActionForm';

export default function Withdraw() {
  return (
    <AmountActionForm
      mode="withdraw"
      title="Withdraw Funds"
      endpoint="/transactions/withdraw"
      buttonLabel="Withdraw"
    />
  );
}