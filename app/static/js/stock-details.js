// stock-details.js
// Handles TradingView initialization, technical charts (RSI/MACD) and UI actions for details_enhanced.html
(function(){
  const logPrefix = '[StockDetails]';
  function initTabs(){
    try {
      const buttons = document.querySelectorAll('#stockDetailTabs button');
      if(buttons.length && window.bootstrap){
        [...buttons].forEach(btn => new bootstrap.Tab(btn));
      }
    } catch(e){ console.warn(logPrefix,'Tab init failed', e); }
  }

  function formatTradingViewSymbol(raw){
    if(!raw) return 'AAPL';
    let symbol = raw;
    if(symbol.endsWith('.OL')){
      const t = symbol.replace('.OL','');
      // TradingView uses OSL: prefix for Oslo Børs tickers
      return `OSL:${t}`;
    }
    if(!symbol.includes(':') && /^[A-Z]{1,5}$/.test(symbol)){
      return `NASDAQ:${symbol}`;
    }
    return symbol;
  }

  function loadTradingView(symbol){
    const container = document.getElementById('tradingview_main_widget');
    if(!container) return;
    const formatted = formatTradingViewSymbol(symbol);

    function createWidget(){
      if(typeof TradingView === 'undefined'){
        return setTimeout(createWidget, 400);
      }
      try {
        new TradingView.widget({
          autosize: true,
          symbol: formatted,
          interval: 'D',
          timezone: 'Europe/Oslo',
          theme: 'light',
          style: '1',
          locale: 'no',
          toolbar_bg: '#f1f3f6',
            enable_publishing: false,
            allow_symbol_change: true,
            container_id: 'tradingview_main_widget',
            hide_side_toolbar: false,
            studies: ['RSI@tv-basicstudies','MACD@tv-basicstudies'],
            loading_screen: { backgroundColor: '#ffffff', foregroundColor: '#2962FF' },
            onChartReady: function(){
              const spinner = document.getElementById('tv-loading-indicator');
              if(spinner) spinner.remove();
            }
        });
      }catch(err){
        console.error(logPrefix,'TradingView widget error', err);
      }
    }

    // Add spinner
    if(!document.getElementById('tv-loading-indicator')){
      const loadDiv = document.createElement('div');
      loadDiv.id='tv-loading-indicator';
      loadDiv.innerHTML = '<div class="p-5 text-center"><div class="spinner-border text-primary"></div><p class="mt-2">Laster graf...</p></div>';
      container.appendChild(loadDiv);
    }
    createWidget();
  }

  function deterministicRandom(seed){
    let h = 0; for(let i=0;i<seed.length;i++){ h = Math.imul(31,h) + seed.charCodeAt(i) | 0; }
    return () => (h = Math.imul(48271, h) + 0x7fffffff & 0x7fffffff) / 0x7fffffff;
  }

  function buildRSI(base, rand){
    const out = []; for(let i=13;i>=0;i--){ const variance=(rand()-0.5)*10; out.push(Math.max(0, Math.min(100, base+variance))); } return out.reverse();
  }

  function buildMACD(baseMacd, baseSignal, rand){
    const macd=[], signal=[]; for(let i=13;i>=0;i--){ const v=(rand()-0.5)*0.2; macd.push(baseMacd+v); signal.push(baseSignal+v*0.5);} return {macd: macd.reverse(), signal: signal.reverse()};
  }

  function createLineChart(el, cfg){
    const existing = Chart.getChart(el); if(existing) existing.destroy();
    return new Chart(el, cfg);
  }

  function initTechnicalCharts(ctx){
    if(!window.Chart) return;
    const { ticker, rsi, macd, macd_signal } = ctx;
    const rand = deterministicRandom(ticker || 'DEMO');
    const rsiData = buildRSI(rsi ?? 50, rand);
    const macdSeries = buildMACD(macd ?? 0, macd_signal ?? 0, rand);

    const rsiCanvas = document.getElementById('rsiChart');
    if(rsiCanvas){
      createLineChart(rsiCanvas, {
        type:'line',
        data:{ labels: Array.from({length: rsiData.length}, (_,i)=>`Dag ${i+1}`), datasets:[{ label:'RSI', data:rsiData, borderColor:'#dc3545', backgroundColor:'rgba(220,53,69,.1)', borderWidth:2, fill:false }]},
        options:{ responsive:true, maintainAspectRatio:false, scales:{ y:{ min:0,max:100 }}, plugins:{ legend:{display:false} } }
      });
    }

    const macdCanvas = document.getElementById('macdChart');
    if(macdCanvas){
      createLineChart(macdCanvas, {
        type:'line',
        data:{ labels: Array.from({length: macdSeries.macd.length}, (_,i)=>`Dag ${i+1}`), datasets:[
          { label:'MACD', data:macdSeries.macd, borderColor:'#007bff', backgroundColor:'rgba(0,123,255,.1)', borderWidth:2, fill:false },
          { label:'Signal', data:macdSeries.signal, borderColor:'#ffc107', backgroundColor:'rgba(255,193,7,.1)', borderWidth:2, fill:false }
        ]},
        options:{ responsive:true, maintainAspectRatio:false }
      });
    }
  }

  function initActions(){
    const favBtn = document.getElementById('add-to-watchlist');
    if(favBtn){
      favBtn.addEventListener('click', async function(){
        const ticker = this.dataset.ticker; if(!ticker) return;
        const orig = this.innerHTML; this.disabled=true; this.innerHTML='<span class="spinner-border spinner-border-sm"></span>';
        try {
          const res = await fetch('/api/watchlist/toggle',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({symbol: ticker})});
          const data = await res.json();
          if(data.success){
            this.innerHTML = data.is_favorite ? '<i class="bi bi-star-fill"></i> I favoritter':'<i class="bi bi-star"></i> Favoritt';
            this.className = data.is_favorite ? 'btn btn-warning':'btn btn-outline-warning';
          } else { this.innerHTML = orig; }
        } catch(e){ console.error(logPrefix,'fav error', e); this.innerHTML=orig; }
        finally { this.disabled=false; }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('[data-stock-details]');
    if(!root) return;
    const ctx = {
      ticker: root.getAttribute('data-ticker'),
      rsi: parseFloat(root.getAttribute('data-rsi')),
      macd: parseFloat(root.getAttribute('data-macd')),
      macd_signal: parseFloat(root.getAttribute('data-macd-signal'))
    };
    initTabs();
    loadTradingView(ctx.ticker);
    // Load technical charts lazily when technical tab shown
    document.addEventListener('shown.bs.tab', e => {
      if(e.target && e.target.getAttribute('data-bs-target') === '#technical'){
        initTechnicalCharts(ctx);
      }
    });
    initActions();
  });
})();
