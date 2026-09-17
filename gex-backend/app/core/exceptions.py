"""Özel hata sınıfları — Build Spec Bölüm 14.1.

Tüm uygulama hataları AppError'dan türer; global handler (main.py) bunları
standart hata zarfına (Bölüm 7.1) çevirir.
"""
from __future__ import annotations


class AppError(Exception):
    """Tüm uygulama hatalarının temel sınıfı."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=403)


class NotFoundError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=404)


class ConflictError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=409)


class BusinessRuleError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, status_code=422)
