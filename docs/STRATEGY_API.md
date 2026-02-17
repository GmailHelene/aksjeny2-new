# Strategy API

Basisendepunkter ligger under `/analysis/api/strategies` og krever innlogget bruker (access_required).

## Oppsummering
| Metode | Path | Beskrivelse |
|--------|------|-------------|
| GET | /analysis/api/strategies | Liste (basic) av strategier for bruker |
| POST | /analysis/api/strategies | Opprett ny strategi |
| GET | /analysis/api/strategies/<id> | Hent full strategi (inkl. regler) |
| PATCH/PUT | /analysis/api/strategies/<id> | Oppdater navn og/eller regler |
| DELETE | /analysis/api/strategies/<id> | Slett strategi |

## Modellfelt
```
Strategy: {
  id: number,
  name: string,
  buy: object,      // buy_rules
  sell: object,     // sell_rules
  risk: object,     // risk_rules
  created_at: ISO8601,
  updated_at: ISO8601
}
```

## Opprett Strategi (POST)
Request:
```json
POST /analysis/api/strategies
Content-Type: application/json
{
  "name": "RSI Breakout",
  "buy": {"indicator":"rsi","condition":"below","value":30},
  "sell": {"indicator":"rsi","condition":"above","value":70},
  "risk": {"stop_loss":5,"take_profit":10}
}
```
Response (201/200):
```json
{ "success": true, "id": 42, "name": "RSI Breakout" }
```
Feil:
- 400: Mangler eller for kort navn (< 2)
- 409: Duplikat navn (case-insensitive)
- 500: DB-feil

## Liste Strategier (GET)
`GET /analysis/api/strategies`
```json
{ "success": true, "strategies": [ {"id":1, "name":"RSI Breakout", "created_at":"..."} ] }
```
(Basic liste mangler regler for lav payload.)

## Hent Full Strategi
`GET /analysis/api/strategies/42`
```json
{ "success": true, "strategy": { "id":42, "name":"RSI Breakout", "buy":{...}, "sell":{...}, "risk":{...}, "created_at":"..." } }
```

## Oppdater (PATCH)
Delvis oppdatering:
```json
PATCH /analysis/api/strategies/42
{
  "name": "RSI Reversal",
  "risk": {"stop_loss":4, "take_profit":12}
}
```
Svar:
```json
{ "success": true, "strategy": { ... oppdatert ... } }
```
Feil:
- 400: Tomt navn / ugyldige felttyper
- 409: Duplikat navn
- 404: Ikke funnet
- 500: DB-feil

## Slett (DELETE)
`DELETE /analysis/api/strategies/42`
```json
{ "success": true, "deleted": 42 }
```

## Eksempelskript (curl)
```bash
# Create
curl -X POST http://localhost:5000/analysis/api/strategies \
  -H 'Content-Type: application/json' -b 'session=<COOKIE>' \
  -d '{"name":"Test SMA","buy":{"indicator":"sma","condition":"crosses_above","value":50},"sell":{"indicator":"sma","condition":"crosses_below","value":50},"risk":{"stop_loss":5,"take_profit":8}}'

# List
curl -X GET http://localhost:5000/analysis/api/strategies -b 'session=<COOKIE>'

# Get full
curl -X GET http://localhost:5000/analysis/api/strategies/42 -b 'session=<COOKIE>'

# Patch name
curl -X PATCH http://localhost:5000/analysis/api/strategies/42 \
  -H 'Content-Type: application/json' -b 'session=<COOKIE>' \
  -d '{"name":"Test SMA v2"}'

# Delete
curl -X DELETE http://localhost:5000/analysis/api/strategies/42 -b 'session=<COOKIE>'
```

## Videre Forbedringer (Forslag)
- Versjonering av strategier
- Historikk / audit trail
- Flere regler (liste i stedet for enkel struktur)
- Integrasjon med backtester endpoint
- Rate limiting / kvoter per bruker

## Strategy Builder UI Hint
Frontend-siden `analysis/strategy_builder.html` bruker:
- POST /analysis/api/strategies for lagring
- GET /analysis/api/strategies ved initial oppfriskning
Planlagt videre: enable "Full visning"-knapp som vil hente `/analysis/api/strategies/<id>` for å fylle inn redigeringsskjema.

