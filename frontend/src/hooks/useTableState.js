import { useCallback, useState } from 'react';

// Minimal hook: standardize loading/error + fetch runner.
// error types:
// - null
// - 'db_unavailable' (5xx)
// - 'coming_soon' (501)
// - 'generic'

export default function useTableState(initialRows = []) {
  const [rows, setRows] = useState(initialRows);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (fn) => {
    setLoading(true);
    setError(null);

    try {
      const data = await fn();
      return data;
    } catch (err) {
      const status = err?.response?.status;
      if (status === 501) setError('coming_soon');
      else if (status === 500 || status === 502 || status === 503) setError('db_unavailable');
      else setError('generic');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    rows,
    setRows,
    loading,
    error,
    run,
    setError,
    setLoading,
  };
}
