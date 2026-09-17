export function MethodologyPage() {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Metodoloji</h1>
        <p className="page-subtitle">Hesaplamaların nasıl yapıldığı ve hangi varsayımlara dayandığı</p>
      </header>

      <div style={{ maxWidth: 720, display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
        <section className="ui-card ui-card--pad meth">
          <h2 className="ui-card__title">Gamma nasıl hesaplanır?</h2>
          <p>
            Veri sağlayıcı hazır gamma veriyorsa doğrudan o kullanılır. Vermiyorsa, her opsiyon için
            standart <strong>Black-Scholes gamma</strong> formülü uygulanır:
          </p>
          <pre className="meth-formula">Γ = N'(d1) / (S · σ · √T)</pre>
          <p className="muted">S: spot fiyat · σ: implied volatility · T: vadeye kalan süre (yıl) · r: risksiz faiz oranı.</p>
        </section>

        <section className="ui-card ui-card--pad meth">
          <h2 className="ui-card__title">Net GEX ve seviyeler</h2>
          <p>
            Her strike için dolar cinsinden gamma exposure hesaplanır ve call/put katkıları toplanarak
            <strong> Net GEX</strong> bulunur. <strong>Gamma Flip</strong>, kümülatif net GEX'in işaret değiştirdiği
            strike'tır. <strong>Call Wall</strong> en yüksek pozitif, <strong>Put Wall</strong> en negatif GEX'e sahip strike'tır.
          </p>
          <pre className="meth-formula">Net_GEX(strike) = Call_GEX − Put_GEX</pre>
        </section>

        <section className="ui-card ui-card--pad meth meth--warn">
          <h2 className="ui-card__title">Önemli varsayım: Dealer işaret konvansiyonu</h2>
          <p>
            Gerçek dealer (market maker) pozisyonları <strong>halka açık değildir</strong>. Sistem, endüstride yaygın
            kabul gören (SqueezeMetrics tarzı) bir <strong>varsayım</strong> kullanır: call OI pozitif, put OI negatif
            GEX katkısı yapar. Bu <em>kesin doğru değil</em>, yaygın kabul görmüş bir tahmindir. Sonuçlar bu çerçevede
            yorumlanmalıdır.
          </p>
        </section>
      </div>
    </div>
  );
}
