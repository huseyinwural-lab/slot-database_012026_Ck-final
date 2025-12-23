// Centralized money-path error code to Turkish message mapping for player app

export const moneyPathErrorMessage = (error) => {
  // Extract info from various error shapes (Axios, standardized, etc.)
  const response = error?.response;
  const data = response?.data;
  
  const status = error?.standardized?.status || error?.status || response?.status;
  
  // Default code from error object (e.g. ERR_BAD_REQUEST)
  let code = error?.standardized?.code || error?.code || 'UNKNOWN_ERROR';

  // Override with API-specific error code if present (FastAPI: detail.error_code)
  if (data?.detail?.error_code) {
    code = data.detail.error_code;
  }

  const map = {
    IDEMPOTENCY_KEY_REUSE_CONFLICT: 'Aynı işlem anahtarı farklı bir istekle kullanıldı. Lütfen sayfayı yenileyip tekrar deneyin.',
    INVALID_STATE_TRANSITION: 'İşlemin durumu değişmiş görünüyor. Sayfa güncellendi.',
    IDEMPOTENCY_KEY_REQUIRED: 'Bu işlem için idempotency anahtarı zorunludur.',
    TX_NOT_FOUND: 'İşlem bulunamadı veya artık geçerli değil.',
    PLAYER_NOT_FOUND: 'Oyuncu kaydı bulunamadı.',
    FEATURE_DISABLED: 'Bu özellik bu tenant için devre dışı.',
    UNAUTHORIZED: 'Oturumunuzun süresi dolmuş olabilir. Lütfen tekrar giriş yapın.',
    LIMIT_EXCEEDED: 'Günlük işlem limiti aşıldı.',
    KYC_DEPOSIT_LIMIT: 'Onaysız hesaplar için günlük yatırma limiti aşıldı.',
    KYC_REQUIRED_FOR_WITHDRAWAL: 'Para çekmek için kimlik doğrulaması gereklidir.'
  };

  if (status === 401) {
    return map.UNAUTHORIZED;
  }

  if (map[code]) return map[code];

  if (!status) {
    return 'Ağ hatası oluştu. Lütfen bağlantınızı kontrol edip tekrar deneyin.';
  }

  if (status >= 500) {
    return 'Sunucu tarafında geçici bir hata oluştu. Lütfen bir süre sonra tekrar deneyin.';
  }

  // Fallback to detail message if it's a simple string
  if (data?.detail && typeof data.detail === 'string') {
      return data.detail;
  }

  return error?.standardized?.message || 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.';
};
