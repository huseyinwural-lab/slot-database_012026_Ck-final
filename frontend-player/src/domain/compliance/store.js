import { create } from 'zustand';
import { trackEvent } from '@/telemetry';

export const useComplianceStore = create((set) => ({
  ageState: 'unknown',
  error: null,
  verifyAge: ({ dob, accepted }) => {
    if (!accepted) {
      set({ ageState: 'failed', error: { code: 'COMPLIANCE_AGE_REQUIRED', message: '18+ onayı gerekli' } });
      return false;
    }
    const birthDate = new Date(dob);
    const now = new Date();
    const age = now.getFullYear() - birthDate.getFullYear();
    const monthDiff = now.getMonth() - birthDate.getMonth();
    const dayDiff = now.getDate() - birthDate.getDate();
    const isAdult = age > 18 || (age === 18 && (monthDiff > 0 || (monthDiff === 0 && dayDiff >= 0)));
    if (!isAdult) {
      set({ ageState: 'failed', error: { code: 'COMPLIANCE_AGE_REQUIRED', message: '18+ doğrulaması gerekli' } });
      return false;
    }
    trackEvent('age_verified', { dob });
    set({ ageState: 'passed', error: null });
    return true;
  },
}));
