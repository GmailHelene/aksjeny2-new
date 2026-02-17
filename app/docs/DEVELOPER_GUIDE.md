# Aksjeradar - Utviklerveiledning

## Arkitektur

### Teknologi-stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL med SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Vanilla JS
- **Deployment**: Railway
- **APIs**: Yahoo Finance, OpenAI

### Prosjektstruktur
```
aksjeradarny/
├── app/
│   ├── models/          # Database-modeller
│   ├── routes/          # API-endepunkter
│   ├── services/        # Forretningslogikk
│   ├── templates/       # HTML-templates
│   ├── static/          # CSS, JS, bilder
│   └── utils/           # Hjelpefunksjoner
├── migrations/          # Database-migrasjoner
├── tests/              # Tester
└── docs/               # Dokumentasjon
```

## Norsk tallformatering

### Implementering
Alle tall må formateres med norsk standard:
- Tusenskiller: space (1 234 567)
- Desimaltegn: komma (1 234,56)
- Valuta: kr-suffix (1 234,56 kr)

### Hjelpefunksjoner
```python
# app/utils/formatters.py
format_number_norwegian(value, decimals=2)
format_currency_norwegian(value)
format_percentage_norwegian(value)
```

### Template-filtre
```html
{{ value|norwegian_number }}
{{ value|norwegian_currency }}
{{ value|norwegian_percentage }}
```

## API-endepunkter

### Autentisering
- POST `/login` - Innlogging
- POST `/register` - Registrering
- GET `/logout` - Utlogging

### Portefølje
- GET `/portfolio` - Vis portefølje
- POST `/portfolio/add` - Legg til aksje
- PUT `/portfolio/update/<id>` - Oppdater posisjon
- DELETE `/portfolio/delete/<id>` - Slett posisjon
- GET `/portfolio/export` - Eksporter data

### Analyse
- GET `/analysis/technical/<symbol>` - Teknisk analyse
- GET `/analysis/ai/<symbol>` - KI-analyse
- GET `/analysis/graham/<symbol>` - Graham-analyse
- GET `/analysis/buffett/<symbol>` - Buffett-analyse
- GET `/analysis/short/<symbol>` - Short-analyse

### Brukerpreferanser
- GET `/api/preferences` - Hent preferanser
- POST `/api/preferences` - Lagre preferanser

## Database-modeller

### User
- id, email, password_hash, created_at
- trial_start, is_premium, exempt_from_trial

### Portfolio
- id, user_id, symbol, shares, purchase_price
- purchase_date, current_price, last_updated

### NotificationSettings
- id, user_id, language, email_alerts
- price_alerts, news_alerts, theme
- number_format, widgets

## Ytelsesoptimalisering

### Caching
- Redis for API-responser (5 min TTL)
- Database query caching
- Frontend localStorage for brukerdata

### Monitoring
```python
from app.services.performance_monitor import monitor_performance

@monitor_performance
def slow_function():
    # Din kode
```

### Best practices
1. Bruk lazy loading for bilder
2. Minifiser CSS/JS i produksjon
3. Implementer pagination for lister
4. Cache statiske data aggressivt

## Testing

### Kjør tester
```bash
pytest tests/
pytest tests/test_formatters.py -v
pytest --cov=app tests/
```

### Testdekning
- Enhtstester for alle services
- Integrasjonstester for API
- E2E-tester for kritiske flyter

## Deployment

### Railway
1. Push til main-branch
2. Railway bygger automatisk
3. Kjører migrasjoner
4. Starter applikasjonen

### Miljøvariabler
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
YAHOO_API_KEY=...
OPENAI_API_KEY=...
```

## Feilsøking

### Vanlige problemer
1. **Import-feil**: Sjekk PYTHONPATH
2. **Database-feil**: Kjør migrasjoner
3. **API-feil**: Sjekk rate limits
4. **Formatering**: Bruk riktige hjelpefunksjoner

### Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Melding")
logger.error("Feil", exc_info=True)
```

## Bidra til prosjektet

1. Fork repository
2. Lag feature-branch
3. Implementer endringer
4. Skriv tester
5. Send pull request

---
*Sist oppdatert: Juli 2025*
