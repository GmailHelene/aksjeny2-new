// Portfolio CRUD actions extracted from index.html inline script
// Handles delete portfolio, remove stock, switch portfolio, widget prefs
(function(){
  let deletePortfolioId = null;
  function getCsrf(){
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  }
  function showToast(message, type){
    if(window.showToast){
      window.showToast(message, type);
    } else {
      console.log('[Toast:'+type+']', message);
    }
  }
  function deletePortfolio(portfolioId){
    deletePortfolioId = portfolioId;
    const modalEl = document.getElementById('confirmDeletePortfolioModal');
    if(!modalEl){
      if(!confirm('Slette portefølje? Dette kan ikke angres.')) return;
      submitPortfolioDeletion();
      return;
    }
    const portfolioName = document.querySelector('h2.mb-1')?.innerText || 'porteføljen';
    modalEl.querySelector('#deletePortfolioName').innerText = portfolioName;
    modalEl.querySelector('#confirmPortfolioName').value='';
    modalEl.querySelector('#confirmDeleteBtn').disabled = true;
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
  }
  function onPortfolioNameInput(ev){
    const input = ev.target.value.trim();
    const expected = document.getElementById('deletePortfolioName').innerText.trim();
    document.getElementById('confirmDeleteBtn').disabled = (input !== expected);
  }
  function submitPortfolioDeletion(){
    if(!deletePortfolioId) return;
    const portfolioCard = document.querySelector(`[data-portfolio-id="${deletePortfolioId}"]`);
    if(portfolioCard){
      portfolioCard.style.opacity='0.5';
      portfolioCard.style.pointerEvents='none';
    }
    fetch(`/portfolio/delete/${deletePortfolioId}`, {
      method:'POST',
      headers:{
        'X-CSRFToken': getCsrf(),
        'Accept':'application/json',
        'Content-Type':'application/json'
      }
    }).then(r=>r.json())
    .then(data=>{
      if(data.success){
        showToast(data.message || 'Portefølje slettet', 'success');
        setTimeout(()=>window.location.href='/portfolio/overview', 500);
      } else {
        if(portfolioCard){
          portfolioCard.style.opacity='1';
          portfolioCard.style.pointerEvents='auto';
        }
        showToast(data.error || 'Kunne ikke slette portefølje', 'error');
      }
    }).catch(err=>{
      console.error('Delete portfolio error', err);
      if(portfolioCard){
        portfolioCard.style.opacity='1';
        portfolioCard.style.pointerEvents='auto';
      }
      showToast('Teknisk feil ved sletting av portefølje', 'error');
    });
  }
  function removeStock(stockId, portfolioId){
    if(!confirm('Er du sikker på at du vil fjerne denne aksjen fra porteføljen?')) return;
    if(!portfolioId){
      alert('Kunne ikke identifisere portefølje-ID');
      return;
    }
    fetch(`/portfolio/${portfolioId}/remove/${stockId}`, {
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'Accept':'application/json',
        'X-CSRFToken': getCsrf()
      }
    }).then(r=>{
      return r.json().catch(()=>({success:false,error:'Ugyldig svar'}));
    }).then(data=>{
      if(data.success){
        showToast('Aksjen ble fjernet', 'success');
        setTimeout(()=>window.location.reload(), 400);
      } else {
        alert('Kunne ikke fjerne aksjen: '+(data.error||'Ukjent feil'));
      }
    }).catch(err=>{
      console.error('Remove stock error', err);
      alert('Det oppstod en feil ved fjerning av aksjen');
    });
  }
  function switchPortfolio(portfolioId){
    window.location.href = `/portfolio?selected=${portfolioId}`;
  }
  function loadWidgetPreferences(){
    fetch('/api/user/preferences')
      .then(r=>r.json())
      .then(data=>{
        let widgets=[]; try{widgets = JSON.parse(data.dashboard_widgets||'[]');}catch(e){widgets=['total-value','profit-loss','alerts'];}
        ['total-value','profit-loss','alerts'].forEach(id=>{
          const el = document.getElementById(`widget-${id}`); if(el){ el.style.display = widgets.includes(id) ? '' : 'none'; }
        });
      })
      .catch(()=>{
        ['total-value','profit-loss','alerts'].forEach(id=>{ const el=document.getElementById(`widget-${id}`); if(el) el.style.display='';});
      });
  }
  document.addEventListener('DOMContentLoaded', loadWidgetPreferences);
  // Expose minimal API
  window.PortfolioCRUD = { deletePortfolio, submitPortfolioDeletion, onPortfolioNameInput, removeStock, switchPortfolio };
})();
