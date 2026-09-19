"""GEX seviyelerini TradingView Pine Script indikatörü olarak dışa aktarır.

NEDEN GÖMÜLÜ VERİ: Pine Script TradingView'in sandbox'ında çalışır ve HTTP
isteği YAPAMAZ — bizim API'mizden canlı veri çekmesi mümkün değil. `request.*`
fonksiyonları yalnızca TradingView'in kendi verisine erişir. (Tek istisna,
TradingView'in onayladığı GitHub depolarından okuyan "Pine Seeds" mekanizması;
onboarding gerektirdiği için pratik değil.)

Bu yüzden seviyeler script'in içine SABİT olarak gömülür. Veri güncellendiğinde
script yeniden üretilmelidir — üretim zamanı script'in başına yazılır.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SymbolLevels:
    """Tek bir sembolün Pine'a gömülecek seviyeleri."""

    ticker: str
    spot: float
    call_wall: float | None = None
    put_wall: float | None = None
    flip: float | None = None
    resistances: list[float] | None = None  # Call Wall dışındakiler
    supports: list[float] | None = None     # Put Wall dışındakiler


def _num(value: float | None) -> str:
    """Pine için sayı; yoksa `na`."""
    return "na" if value is None else f"{value:.4f}".rstrip("0").rstrip(".")


def _slot(values: list[float] | None, index: int) -> float | None:
    if not values or index >= len(values):
        return None
    return values[index]


def build_pine_script(symbols: list[SymbolLevels], title: str = "GEX Seviyeleri") -> str:
    """Çok sembollü Pine v6 indikatörü üretir.

    Script `syminfo.ticker` ile aktif sembolü tanır ve o sembolün seviyelerini
    çizer; tanımadığı sembolde sessizce hiçbir şey çizmez.
    """
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    a = lines.append

    a("//@version=6")
    a(f'indicator("{title}", overlay = true, max_labels_count = 500)')
    a("")
    a("// ─────────────────────────────────────────────────────────────")
    a("//  GEX Analiz Platformu — otomatik üretildi")
    a(f"//  Üretim zamanı : {generated}")
    a(f"//  Sembol sayısı : {len(symbols)}")
    a("//")
    a("//  ÖNEMLİ: Pine Script dışarıdan veri çekemez; seviyeler bu script'e")
    a("//  SABİT gömülüdür. GEX verisi değişince script'i yeniden üretin.")
    a("// ─────────────────────────────────────────────────────────────")
    a("")
    a("// ── Görünüm ayarları ──")
    a('showLabels = input.bool(true,  "Etiketleri göster")')
    a('lineWidth  = input.int(1, "Çizgi kalınlığı", minval = 1, maxval = 4)')
    a('resColor   = input.color(color.new(#f0616d, 0), "Direnç")')
    a('supColor   = input.color(color.new(#3fb950, 0), "Destek")')
    a('flipColor  = input.color(color.new(#d9a441, 0), "Gamma Flip")')
    a("")
    a("// ── Seviye tablosu (sembol bazlı) ──")
    a("f_gexLevels() =>")
    a("    float cw = na")
    a("    float r1 = na")
    a("    float r2 = na")
    a("    float pw = na")
    a("    float s1 = na")
    a("    float s2 = na")
    a("    float fl = na")

    for i, sym in enumerate(symbols):
        keyword = "if" if i == 0 else "else if"
        a(f'    {keyword} syminfo.ticker == "{sym.ticker}"')
        a(f"        cw := {_num(sym.call_wall)}")
        a(f"        r1 := {_num(_slot(sym.resistances, 0))}")
        a(f"        r2 := {_num(_slot(sym.resistances, 1))}")
        a(f"        pw := {_num(sym.put_wall)}")
        a(f"        s1 := {_num(_slot(sym.supports, 0))}")
        a(f"        s2 := {_num(_slot(sym.supports, 1))}")
        a(f"        fl := {_num(sym.flip)}")

    a("    [cw, r1, r2, pw, s1, s2, fl]")
    a("")
    a("[callWall, res1, res2, putWall, sup1, sup2, gammaFlip] = f_gexLevels()")
    a("")
    a("// ── Çizimler ── (sabit değer -> yatay çizgi)")
    a('p_cw = plot(callWall,   "Call Wall",  color = resColor,  linewidth = lineWidth + 1, style = plot.style_linebr)')
    a('p_r1 = plot(res1,       "1. Direnç",  color = resColor,  linewidth = lineWidth,     style = plot.style_linebr)')
    a('p_r2 = plot(res2,       "2. Direnç",  color = resColor,  linewidth = lineWidth,     style = plot.style_linebr)')
    a('p_pw = plot(putWall,    "Put Wall",   color = supColor,  linewidth = lineWidth + 1, style = plot.style_linebr)')
    a('p_s1 = plot(sup1,       "1. Destek",  color = supColor,  linewidth = lineWidth,     style = plot.style_linebr)')
    a('p_s2 = plot(sup2,       "2. Destek",  color = supColor,  linewidth = lineWidth,     style = plot.style_linebr)')
    a('p_fl = plot(gammaFlip,  "Gamma Flip", color = flipColor, linewidth = lineWidth,     style = plot.style_linebr)')
    a("")
    a("// Call Wall ile Put Wall arası: gamma bölgesi")
    a("fill(p_cw, p_pw, color = color.new(#5b8def, 94), title = \"Gamma bölgesi\")")
    a("")
    a("// ── Son barda etiketler ──")
    a("f_label(_price, _txt, _col) =>")
    a("    if showLabels and not na(_price) and barstate.islast")
    a("        label.new(bar_index + 3, _price, _txt + \"  \" + str.tostring(_price, format.mintick),")
    a("             xloc = xloc.bar_index, style = label.style_label_left,")
    a("             color = color.new(_col, 85), textcolor = _col, size = size.small)")
    a("")
    a('f_label(callWall,  "Call Wall",  resColor)')
    a('f_label(res1,      "1. Direnç",  resColor)')
    a('f_label(res2,      "2. Direnç",  resColor)')
    a('f_label(putWall,   "Put Wall",   supColor)')
    a('f_label(sup1,      "1. Destek",  supColor)')
    a('f_label(sup2,      "2. Destek",  supColor)')
    a('f_label(gammaFlip, "Gamma Flip", flipColor)')
    a("")
    a("// ── Uyarılar ──")
    a("alertcondition(not na(callWall)  and ta.crossover(close, callWall),   \"Call Wall yukarı kırıldı\",  \"Fiyat Call Wall üstüne çıktı\")")
    a("alertcondition(not na(putWall)   and ta.crossunder(close, putWall),   \"Put Wall aşağı kırıldı\",    \"Fiyat Put Wall altına indi\")")
    a("alertcondition(not na(gammaFlip) and ta.cross(close, gammaFlip),      \"Gamma Flip kesişti\",        \"Fiyat gamma flip seviyesini kesti\")")
    a("")

    return "\n".join(lines)
