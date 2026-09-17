"""Router toplama noktası.

Her router kendi dosyasında tanımlanır; burada tek listede toplanır ve main.py
`/api` öneki ile bağlar (Build Spec Bölüm 6.2, 7.1).

Skeleton aşamasında router'lar tanımlı ama iş mantığı Faz 4+ ile doldurulacak
(bkz. her dosyadaki TODO'lar ve Bölüm 19 Build Roadmap).
"""
from __future__ import annotations

from app.routers import (
    alerts,
    auth,
    dashboard,
    data_status,
    journal,
    notifications,
    settings,
    symbols,
    watchlist,
)

all_routers = [
    auth.router,
    dashboard.router,
    symbols.router,
    watchlist.router,
    alerts.router,
    notifications.router,
    journal.router,
    data_status.router,
    settings.router,
]
