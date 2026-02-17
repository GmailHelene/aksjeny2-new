# Flask URL_FOR Error Fix - My Subscription Page

## Problem:
```
ValueError: When specifying '_scheme', '_external' must be True.
```

Feilen oppstod i `/my-subscription` siden på grunn av feil bruk av Flask's `url_for()` funksjon.

## Root Cause:
I `app/templates/subscription/my-subscription.html` var det flere steder hvor `url_for()` ble kalt med invalid parametere:

```jinja2
url_for('pricing.pricing_page', _external=False, _scheme='')
```

Dette er ugyldig fordi når du spesifiserer `_scheme` parameter, må `_external` være `True`, ikke `False`.

## Solution:
Fjernet de kompliserte og unødvendige `_external=False, _scheme=''` parameterne og brukte enkel `url_for()` syntaks:

### Before (❌ Feil):
```jinja2
<a href="{{ url_for('pricing.pricing_page') if url_for('pricing.pricing_page', _external=False, _scheme='') else '#' }}" class="btn btn-primary">
```

### After (✅ Riktig):
```jinja2
<a href="{{ url_for('pricing.pricing_page') }}" class="btn btn-primary">
```

## Files Changed:
- `app/templates/subscription/my-subscription.html` - Fikset 4 forskjellige `url_for()` kall

## Fixed Locations:
1. Line ~28: "Oppgrader til Premium" knapp
2. Line ~77: Månedlig abonnement "Velg" knapp  
3. Line ~88: Årlig abonnement "Velg" knapp
4. Line ~98: Livstid abonnement "Velg" knapp
5. Line ~109: "Avbryt abonnement" knapp

## Verification:
✅ `/my-subscription` side laster nå uten feil
✅ Alle knapper peker til riktige sider
✅ Flask URL-generering fungerer normalt

## Prevention:
Unngå bruk av `_scheme` og `_external` parametere i `url_for()` med mindre du spesifikt trenger eksterne URL-er med custom scheme.
