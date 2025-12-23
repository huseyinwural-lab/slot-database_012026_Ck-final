// Centralized money-path error code to Turkish message mapping for player app

export const moneyPathErrorMessage = (error) => {
  const code = error?.standardized?.code || error?.code || 'UNKNOWN_ERROR';
  const status = error?.standardized?.status || error?.status;

  const map = {
    IDEMPOTENCY_KEY_REUSE_CONFLICT: 'Aynı işlem anahtarı farklı bir istekle kullanıldı. Lütfen sayfayı yenileyip tekrar deneyin.',
    INVALID_STATE_TRANSITION: 'İşlemin durumu değişmiş görünüyor. Sayfa güncellendi.',
    IDEMPOTENCY_KEY_REQUIRED: 'Bu işlem için idempotency anahtarı zorunludur.',
    TX_NOT_FOUND: 'İşlem bulunamadı veya artık geçerli değil.',
    PLAYER_NOT_FOUND: 'Oyuncu kaydı bulunamadı.',
    FEATURE_DISABLED: 'Bu özellik bu tenant için devre dışı.',
    UNAUTHORIZED: 'Oturumunuzun süresi dolmuş olabilir. Lütfen tekrar giriş yapın.',
    LIMIT_EXCEEDED: 'Günlük işlem limiti aşıldı.',
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

  return error?.standardized?.message || 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.';
};
