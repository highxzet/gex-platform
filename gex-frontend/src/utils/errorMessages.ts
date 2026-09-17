/**
 * Hata kodundan mesaja çeviri — Build Spec Bölüm 10.6.
 * Backend `error.code` alanlarıyla BİRE BİR eşleşmelidir (yeni kod eklenince buraya da eklenir).
 */
export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: "E-posta veya şifre hatalı.",
  ACCOUNT_LOCKED: "Çok fazla başarısız deneme. 15 dakika sonra tekrar deneyin.",
  TOKEN_EXPIRED: "Oturumunuzun süresi doldu, tekrar giriş yapın.",
  TOKEN_INVALID: "Geçersiz oturum.",
  SYMBOL_NOT_FOUND: "'{symbol}' sembolü bulunamadı veya izleme listenizde değil.",
  NO_OPTIONS_DATA: "Bu sembol için opsiyon verisi bulunmuyor.",
  ALREADY_IN_WATCHLIST: "Bu sembol zaten izleme listenizde.",
  INTERNAL_ERROR: "Bir şeyler ters gitti. Lütfen tekrar deneyin.",
};

export function messageForCode(code: string, fallback?: string): string {
  return ERROR_MESSAGES[code] ?? fallback ?? "Beklenmeyen bir hata oluştu.";
}
