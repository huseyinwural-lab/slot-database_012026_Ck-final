import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const withdrawalSchema = z.object({
  amount: z.coerce
    .number()
    .min(10, 'Minimum withdrawal amount is 10')
    .max(10000, 'Maximum withdrawal amount is 10,000'),
  accountHolderName: z.string()
    .min(3, 'Account holder name is required')
    .max(50, 'Name must be less than 50 characters'),
  accountNumber: z.string()
    .regex(/^\d{8,17}$/, 'Invalid account number'),
  bankCode: z.string()
    .min(1, 'Bank code is required'),
  branchCode: z.string()
    .min(1, 'Branch/Sort code is required'),
  countryCode: z.string()
    .regex(/^[A-Z]{2}$/, 'Invalid country code'),
  currencyCode: z.string()
    .regex(/^[A-Z]{3}$/, 'Invalid currency code'),
});

export function WithdrawalForm({ playerId, playerEmail, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const form = useForm({
    resolver: zodResolver(withdrawalSchema),
    defaultValues: {
      amount: '',
      accountHolderName: '',
      accountNumber: '',
      bankCode: '',
      branchCode: '',
      countryCode: 'US',
      currencyCode: 'USD',
    },
  });

  async function onSubmit(values) {
    setIsSubmitting(true);
    setResult(null);

    try {
      const amountInMinorUnits = Math.round(values.amount * 100);
      const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

      const response = await fetch(`${API_BASE}/api/payouts/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add Auth header if needed, usually managed by interceptor or cookie
          // Assuming cookie or local storage token
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          player_id: playerId,
          amount: amountInMinorUnits,
          currency: values.currencyCode,
          player_email: playerEmail,
          bank_account: {
            account_holder_name: values.accountHolderName,
            account_number: values.accountNumber,
            bank_code: values.bankCode,
            branch_code: values.branchCode,
            country_code: values.countryCode,
            currency_code: values.currencyCode,
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
        message: `Withdrawal of ${values.amount} ${values.currencyCode} submitted successfully. Your payout ID is ${data.payout_id}.`,
      });

      form.reset();

      if (onSuccess) {
        onSuccess(data);
      }
    } catch (error) {
      setResult({
        type: 'error',
        message: error.message || 'An error occurred during withdrawal submission.',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Request Withdrawal</CardTitle>
        <CardDescription>
          Withdraw your winnings to your bank account. Payouts typically arrive within 1-2 business days.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {result && (
          <Alert className={`mb-6 ${result.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            {result.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription className={result.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {result.message}
            </AlertDescription>
          </Alert>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Withdrawal Amount</FormLabel>
                  <FormControl>
                    <div className="flex items-center">
                      <Input
                        type="number"
                        placeholder="100.00"
                        step="0.01"
                        min="0"
                        {...field}
                      />
                      <span className="ml-3 text-gray-600">USD</span>
                    </div>
                  </FormControl>
                  <FormDescription>
                    Minimum: $10, Maximum: $10,000
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-4 border-t pt-4">
              <h3 className="font-semibold text-lg">Bank Account Details</h3>

              <FormField
                control={form.control}
                name="accountHolderName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Account Holder Name</FormLabel>
                    <FormControl>
                      <Input placeholder="John Doe" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="accountNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Account Number</FormLabel>
                    <FormControl>
                      <Input placeholder="123456789" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="bankCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Bank Code</FormLabel>
                      <FormControl>
                        <Input placeholder="021000021" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="branchCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Branch Code</FormLabel>
                      <FormControl>
                        <Input placeholder="001" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="countryCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Country Code</FormLabel>
                      <FormControl>
                        <Input placeholder="US" maxLength="2" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="currencyCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Currency</FormLabel>
                      <FormControl>
                        <Input placeholder="USD" maxLength="3" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full"
            >
              {isSubmitting ? (
                <>
                  <Clock className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Request Withdrawal'
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
