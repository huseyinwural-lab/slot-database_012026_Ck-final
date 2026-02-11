export const BalancePill = ({ balance, currency }) => (
  <div
    className="flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-1 text-sm"
    data-testid="balance-pill"
  >
    <span className="text-white/70" data-testid="balance-label">Bakiye</span>
    <span className="font-semibold text-white" data-testid="balance-value">{Number(balance).toFixed(2)} {currency}</span>
  </div>
);
