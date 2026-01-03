import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';

export function WithdrawalForm({ playerId, playerEmail, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  
  // Local state instead of react-hook-form/zod to reduce deps if they are missing too
  // But react-hook-form was in package.json in playbook. 
  // Let's assume standard deps are fine, but UI components are missing.
  // We'll use simple controlled inputs for safety.
  const [formData, setFormData] = useState({
    amount: '',
    accountHolderName: '',
    accountNumber: '',
    bankCode: '',
    branchCode: '',
    countryCode: 'US',
    currencyCode: 'USD',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  async function onSubmit(e) {
    e.preventDefault();
    setIsSubmitting(true);
    setResult(null);

    try {
      const amountInMinorUnits = Math.round(parseFloat(formData.amount) * 100);
      const response = await fetch(`/api/v1/payouts/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('player_token')}`
        },
        body: JSON.stringify({
          player_id: playerId,
          amount: amountInMinorUnits,
          currency: formData.currencyCode,
          player_email: playerEmail,
          bank_account: {
            account_holder_name: formData.accountHolderName,
            account_number: formData.accountNumber,
            bank_code: formData.bankCode,
            branch_code: formData.branchCode,
            country_code: formData.countryCode,
            currency_code: formData.currencyCode,
          },
          description: `Casino withdrawal for ${playerId}`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Withdrawal submission failed');
      }

      const data = await response.json();

      setResult({
        type: 'success',
        data: data,
        message: `Withdrawal submitted. ID: ${data.payout_id}`,
      });

      if (onSuccess) {
        onSuccess(data);
      }
    } catch (error) {
      setResult({
        type: 'error',
        message: error.message || 'Error submitting withdrawal.',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="bg-secondary/20 p-6 rounded-xl border border-white/5">
      <h3 className="text-xl font-semibold mb-4 text-white">Request Withdrawal</h3>
      
      {result && (
        <div className={`mb-4 p-3 rounded-lg text-sm flex items-center gap-2 ${result.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
          {result.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {result.message}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1">Withdrawal Amount</label>
          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            placeholder="100.00"
            className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white focus:border-primary focus:outline-none"
            required
            min="10"
          />
        </div>

        <div className="pt-4 border-t border-white/10">
          <h4 className="font-semibold text-lg mb-3 text-white">Bank Account Details</h4>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-muted-foreground mb-1">Account Holder Name</label>
              <input
                type="text"
                name="accountHolderName"
                value={formData.accountHolderName}
                onChange={handleChange}
                placeholder="John Doe"
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm text-muted-foreground mb-1">Account Number</label>
              <input
                type="text"
                name="accountNumber"
                value={formData.accountNumber}
                onChange={handleChange}
                placeholder="123456789"
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Bank Code</label>
                <input
                  type="text"
                  name="bankCode"
                  value={formData.bankCode}
                  onChange={handleChange}
                  placeholder="021000021"
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Branch Code</label>
                <input
                  type="text"
                  name="branchCode"
                  value={formData.branchCode}
                  onChange={handleChange}
                  placeholder="001"
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Country</label>
                <input
                  type="text"
                  name="countryCode"
                  value={formData.countryCode}
                  onChange={handleChange}
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Currency</label>
                <input
                  type="text"
                  name="currencyCode"
                  value={formData.currencyCode}
                  onChange={handleChange}
                  className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
        >
          {isSubmitting && <Clock className="w-4 h-4 animate-spin" />}
          {isSubmitting ? 'Processing...' : 'Request Withdrawal'}
        </button>
      </form>
    </div>
  );
}
