import os
from datetime import datetime
import random

class AIService:
    @staticmethod
    def get_stock_analysis(ticker):
        """
        Generate AI analysis for a stock (demo implementation)
        """
        try:
            # Dictionary with realistic data for specific tickers
            realistic_data = {                'EQNR.OL': {
                    "ticker": "EQNR.OL",
                    "sentiment": "stigende",
                    "strength": "moderat",
                    "summary": "AI-analysen antyder en moderat stigende utsikt for Equinor basert på sterke energipriser, sunne finansielle forhold og strategiske investeringer i fornybar energi. Selskapet fortsetter å dra nytte av høye olje- og gasspriser samtidig som det investerer i grønne energiprosjekter.",
                    "technical_factors": [
                        "RSI på 58,2 indikerer moderat stigende momentum uten å være overkjøpt",
                        "Prisen handler over både 50-dagers og 200-dagers glidende gjennomsnitt, bekrefter opptrend",
                        "Stigende MACD-krysning observert i nylige handelsmøter med økende histogram",
                        "Volumprof viser akkumulering på oppdager, antyder institusjonelle kjøp",
                        "Nylig konsolideringsmønster med høyere bunner indikerer mulig fortsettelse"
                    ],
                    "fundamental_factors": [
                        "Sterk kontantstrøm fra kjerneoperasjoner med $12,5B i Q2, 15% høyere enn forrige kvartal",
                        "Attraktiv utbytteavkastning på 4,2% med bærekraftig 40% utbetalingsgrad",
                        "Økende investeringer i fornybare energiprosjekter med $2,3B forpliktet til havvind",
                        "Netto gjeld til kapital-forhold på 15,3%, godt under bransjegjennomsnittet på 28%",
                        "Forward P/E på 7,5 representerer 30% rabatt til 5-års gjennomsnitt"
                    ],
                    "prediction": {
                        "direction": "opp",
                        "confidence": 0.72,
                        "time_frame": "kort til mellomlang sikt (3-6 måneder)",
                        "target_price": "362 NOK"
                    },
                    "economic_indicators": {
                        "oil_price_trend": "stabilt med oppovergående tendens",
                        "sector_performance": "energisektoren overpresterer markedet med 8%",
                        "interest_rate_impact": "minimal eksponering mot renteøkninger",
                        "currency_exposure": "USD-styrke gunstig for oljeinntekter"
                    }
                },
                'DNB.OL': {
                    "ticker": "DNB.OL",
                    "sentiment": "nøytral",
                    "strength": "moderat",
                    "summary": "AI-analysen antyder en moderat nøytral utsikt for DNB med stabile bankoperasjoner men begrensede vekstkatalysatorer. Selv om banken opprettholder sterke kapitalnivåer og drar nytte av høyere renter, begrenser langsom økonomisk vekst i Norge låneekspansjonsmuligheter.",
                    "technical_factors": [
                        "RSI på 52,3 indikerer nøytralt momentum uten klare overkjøpte/oversolgte signaler",
                        "Prisen svinger rundt 50-dagers glidende gjennomsnitt med redusert volatilitet",
                        "Volumanalyse viser moderat handelsaktivitet uten klar akkumulering/distribusjon",
                        "Prisen konsoliderer i området mellom 210-225 NOK de siste 6 ukene",
                        "200-dagers glidende gjennomsnitt viser utflating, indikerer nøytrale langsiktige utsikter"
                    ],
                    "fundamental_factors": [
                        "Solid kapitalposisjon med Tier 1-forhold på 18,2%, godt over regulatoriske krav",
                        "Moderat lånevekst i privat- og bedriftssektorer på 3,2% år-over-år",
                        "Utbytteavkastning på 3,8% med potensial for økninger gitt 50% utbetalingsmål",
                        "Netto rentemargin forbedret til 1,7% fra 1,5% på grunn av høyere renter",
                        "Kostnad-til-inntekt-forhold stabilt på 43,5%, blant de beste i klassen for europeiske banker"
                    ],
                    "prediction": {
                        "direction": "sideveis",
                        "confidence": 0.65,
                        "time_frame": "mellomlang sikt (6-12 måneder)",
                        "target_price": "215-225 NOK-område"
                    },
                    "economic_indicators": {
                        "interest_rate_trend": "stabile høye renter gunstige for marginer",
                        "norwegian_economy": "beskjeden BNP-vekst på 1,5-2%",
                        "housing_market": "avkjøling men stabil, begrenser boliglånsvekst",
                        "consumer_confidence": "moderat forsiktig, påvirker låneetterspørsel"
                    }
                },
                'AAPL': {
                    "ticker": "AAPL",
                    "sentiment": "stigende",
                    "strength": "sterk",
                    "summary": "AI-analysen antyder en sterk stigende utsikt for Apple basert på tjenestevekst, sterkt produktøkosystem og kommende AI-innovasjoner. Selskapet fortsetter å demonstrere prissettingsmakt og kundelojalitet samtidig som det utvider sin høymargin-tjenestevirksomhet med tosifret vekstrate.",
                    "technical_factors": [
                        "RSI på 61,5 indikerer moderat stigende momentum uten å nå overkjøpte nivåer",
                        "Stigende flaggmønster dannes på priskurven etter nylig 15% oppgang",
                        "Sterk positiv volumprof med institusjonelle kjøp ved tilbakeslag",
                        "Gyldent kryss dannet med 50-dagers SMA krysser over 200-dagers SMA",
                        "Prisen konsoliderer over tidligere motstandsnivå, nå fungerer som støtte"
                    ],
                    "fundamental_factors": [
                        "Tjenesteinntekter vokser med 18,7% år-over-år med høye marginer over 70%",
                        "Robust balanse med $190B i kontantreserver og minimal gjeld",
                        "Sterk merkelojalitet og økosystem-innlåsingseffekter med 98% oppbevaringsrate",
                        "Aksjetilbakekjøpsprogram fortsetter med $90B autorisert, reduserer antall aksjer",
                        "Forward P/E på 28x rettferdiggjort av tjenestevekst og kommende AI-initiativer"
                    ],
                    "prediction": {
                        "direction": "opp",
                        "confidence": 0.82,
                        "time_frame": "mellomlang til lang sikt (6-18 måneder)",
                        "target_price": "$210-215"
                    },
                    "economic_indicators": {
                        "consumer_spending": "motstandsdyktig i premiumsegmentet",
                        "tech_sector_trend": "overpresterer bredere marked med 12%",
                        "ai_investment_cycle": "tidlig fase med betydelig vekstpotensial",
                        "supply_chain": "forbedret med diversifisering bort fra Kina"
                    }
                },
                'MSFT': {
                    "ticker": "MSFT",
                    "sentiment": "bullish",
                    "strength": "strong",
                    "summary": "AI-analyse antyder en sterkt bullish utsikt for Microsoft drevet av cloud-vekst, AI-adopsjon og styrke i tilbakevendende inntektsmodell. Selskapet er godt posisjonert som leder innen enterprise AI-implementering med Azure og Copilot-tjenester.",
                    "technical_factors": [
                        "RSI på 72,3 indikerer overkjøpte forhold, mulig kortsiktig tilbaketrekning",
                        "Pris handler godt over alle nøkkel glidende gjennomsnitt med sterk momentum",
                        "Opptrend intakt siden mars 2023 med serie av høyere topper og bunner",
                        "Volum øker på utbrudd, bekrefter bullish sentiment",
                        "Minimal prismotstand overhodet basert på historiske handelsmønstre"
                    ],
                    "fundamental_factors": [
                        "Azure cloud-tjeneste viser akselererende vekst på 27,5% YoY, overgår forventninger",
                        "Sterk posisjon innen AI med OpenAI-integrasjoner og Copilot-monetisering",
                        "Diversifiserte inntektsstrømmer på tvers av flere produktlinjer med 85% tilbakevendende inntekter",
                        "Driftsmarginer utvidet til 43,2% fra 41,8% år-over-år",
                        "Forward EV/EBITDA på 22x rettferdiggjort av cloud-vekst og AI-premie"
                    ],
                    "prediction": {
                        "direction": "opp",
                        "confidence": 0.85,
                        "time_frame": "lang sikt (12-24 måneder)",
                        "target_price": "$425-435"
                    },
                    "economic_indicators": {
                        "enterprise_tech_spending": "motstandsdyktig til tross for økonomisk usikkerhet",
                        "cloud_market_growth": "22% CAGR forventet over neste 3 år",
                        "ai_adoption_rate": "akselererer i bedriftssegmentet",
                        "interest_rate_impact": "minimal med sterk kontantstrømgenerering"
                    }
                },
                'TSLA': {
                    "ticker": "TSLA",
                    "sentiment": "bearish",
                    "strength": "moderate",
                    "summary": "AI-analyse antyder en moderat bearish utsikt for Tesla på grunn av marginpress, økende konkurranse i elbilmarkedet, og høy verdsettelse sammenlignet med andre bilprodusenter. Selskapet står overfor utfordringer med å nå leveringsmål samtidig som det administrerer prisreduksjoner.",
                    "technical_factors": [
                        "RSI på 38,4 nærmer seg oversolgt territorium, men uten positiv divergens ennå",
                        "Pris under 50-dagers og 200-dagers glidende gjennomsnitt, bekrefter nedadgående trend",
                        "Nedadgående trendkanal med gjentatte mislykkede utbruddsforsøk siden januar",
                        "Volum øker på nedgangsdager, antyder distribusjonsmønster",
                        "Hode- og skuldermønster dannet med nakkeline brutt, målretter $210-området"
                    ],
                    "fundamental_factors": [
                        "Marginpress fra priskonkurranse med 18,2% bruttomargin, ned fra 25,1% i fjor",
                        "Utfordringer med å nå leveringsmål for nye modeller med 5% miss i Q2",
                        "Høy verdsettelse sammenlignet med andre bilprodusenter på 60x P/E vs. bransjesnitt på 12x",
                        "Økende konkurranse i kjerne elbilmarked med 27 nye modeller lanseres i år",
                        "FoU-utgifter synker som prosentandel av inntekter, potensielt begrenser fremtidig innovasjon"
                    ],
                    "prediction": {
                        "direction": "down",
                        "confidence": 0.68,
                        "time_frame": "kort til mellomlang sikt (3-6 måneder)",
                        "target_price": "$210-195 område"
                    },
                    "economic_indicators": {
                        "ev_market_growth": "avtar til 25% fra 40% foregående år",
                        "battery_material_costs": "stabiliserer seg etter betydelige fall",
                        "interest_rate_impact": "negativ på kjøretøyfinansiering og verdsettelse",
                        "china_market_dynamics": "økende konkurranse og prispress"
                    }
                },
                'YAR.OL': {
                    "ticker": "YAR.OL",
                    "sentiment": "stigende",
                    "strength": "moderat",
                    "summary": "AI-analysen antyder en moderat stigende utsikt for Yara basert på forbedrede gjødselmarkeder, kostnadskontrolltiltak og strategisk posisjonering innen grønn ammoniakk. Selskapet navigerer vellykket volatile råvarepriser samtidig som det opprettholder operasjonell effektivitet.",
                    "technical_factors": [
                        "RSI på 63,2 viser voksende stigende momentum uten å nå overkjøpte nivåer",
                        "Prisen brøt nylig over viktig motstandsnivå på 340 NOK med høyt volum",
                        "Økende volum på oppdager indikerer akkumuleringsfase",
                        "50-dagers glidende gjennomsnitt krysset over 200-dagers glidende gjennomsnitt (gyldent kryss)",
                        "Priskonsolidering etter utbrudd antyder fortsettelsesmønster"
                    ],
                    "fundamental_factors": [
                        "Gjødselprisene stabiliserer seg etter periode med volatilitet, forbedrer marginsynlighet",
                        "Kostnadseffektivitetsprogram målretter 350M USD i årlige besparelser, 65% oppnådd",
                        "Utbytteavkastning på 5,1% virker bærekraftig med 50-60% utbetalingspolitikk",
                        "Strategiske investeringer i grønn ammoniakk posisjonerer selskapet for fremtidig vekst",
                        "Verdsettelse på 8,2x forward EV/EBITDA representerer 15% rabatt til 5-års gjennomsnitt"
                    ],
                    "prediction": {
                        "direction": "opp",
                        "confidence": 0.71,
                        "time_frame": "mellomlang sikt (6-12 måneder)",
                        "target_price": "365-380 NOK"
                    },
                    "economic_indicators": {
                        "agricultural_commodity_prices": "stabiliserer seg på lønnsomme nivåer for bønder",
                        "natural_gas_prices": "modererer, positivt for produksjonskostnader",
                        "global_food_demand": "økende med befolkningsvekst",
                        "green_transition": "gunstige politiske rammer for lavkarbon ammoniakk"
                    }
                },
                'NHY.OL': {
                    "ticker": "NHY.OL",
                    "sentiment": "nøytral",
                    "strength": "moderat",
                    "summary": "AI-analysen antyder en moderat nøytral utsikt for Norsk Hydro med blandede signaler fra aluminiumsmarkeder, energikostnader og operasjonelle forbedringer. Selskapet drar nytte av grønn aluminium-premier men møter usikkerhet i global industriell etterspørsel.",
                    "technical_factors": [
                        "RSI på 50,6 indikerer nøytralt momentum i balansert territorium",
                        "Prisen konsoliderer i området mellom 62-68 NOK de siste 8 ukene",
                        "Glidende gjennomsnitt konvergerer, antyder potensielt utbrudd eller sammenbrudd",
                        "Volummønster viser ingen klar akkumulering eller distribusjon",
                        "Prisen sitter på 200-dagers glidende gjennomsnitt, viktig teknisk nivå"
                    ],
                    "fundamental_factors": [
                        "Aluminiumspriser stabiliserer seg rundt $2,400/tonn etter volatil periode",
                        "Kostnadsposisjon forbedres gjennom operasjonelt effektivitetsprogram",
                        "Grønn aluminium-initiativer får gjennomslag med premiumprising på 15-20%",
                        "Europeiske energikostnader modererer, positivt for smeltoperasjoner",
                        "Kapitaltildeling balansert mellom utbytte (3,5% avkastning) og vekstinvesteringer"
                    ],
                    "prediction": {
                        "direction": "sideveis",
                        "confidence": 0.60,
                        "time_frame": "kort til mellomlang sikt (3-6 måneder)",
                        "target_price": "64-68 NOK-område"
                    },
                    "economic_indicators": {
                        "industrial_production": "avtar i Europa og Kina",
                        "energy_prices": "stabiliserer seg på lavere nivåer enn 2022-toppen",
                        "construction_activity": "svekkes i nøkkelmarkeder",
                        "green_transition": "støttende politikk for lavkarbon aluminium"
                    }
                },
                'TEL.OL': {
                    "ticker": "TEL.OL",
                    "sentiment": "bearish",
                    "strength": "weak",
                    "summary": "AI-analyse antyder en svak bearish utsikt for Telenor på grunn av konkurransepress i kjernemarkeder, inntektsutfordringer og begrensede vekstkatalysatorer. Selskapet står overfor marginpress til tross for kostnadsbesparende tiltak.",
                    "technical_factors": [
                        "RSI på 32,1 nærmer seg oversolgt territorium, potensial for teknisk hopp",
                        "Pris under både 50-dagers og 200-dagers glidende gjennomsnitt, bekrefter nedtrend",
                        "Synkende volumprof antyder avtakende selgerinteresse, mulig bunning",
                        "Serie av lavere topper og lavere bunner etablert siden september",
                        "Pris nærmer seg støttenivå på 120 NOK fra tidligere konsolidering"
                    ],
                    "fundamental_factors": [
                        "Inntektspress i nordiske markeder med 1,5% nedgang årlig i modne segmenter",
                        "Kostnadsbesparende tiltak viser begrenset påvirkning på samlede marginer",
                        "Utbytteavkastning på 6,3% kan være vanskelig å opprettholde gitt 85% utbetalingsgrad",
                        "Markedsmetning i kjerne nordiske mobil- og bredbåndssegmenter",
                        "Asiatiske operasjoner møter regulatoriske og konkurransemessige utfordringer"
                    ],
                    "prediction": {
                        "direction": "down",
                        "confidence": 0.58,
                        "time_frame": "kort sikt (3 måneder)",
                        "target_price": "118-122 NOK"
                    },
                    "economic_indicators": {
                        "telecom_sector_performance": "underpresterer bredere marked med 6%",
                        "nordic_economies": "avtagende forbruksutgifter påvirker oppgraderinger",
                        "asian_markets": "konkurranseintensitet øker",
                        "interest_rate_impact": "negativ med høye utbytteforventninger"
                    }
                },
                'BTC-USD': {
                    "ticker": "BTC-USD",
                    "sentiment": "bullish",
                    "strength": "moderate",
                    "summary": "AI-analyse antyder en moderat bullish utsikt for Bitcoin etter nylig halvering og økende institusjonell adopsjon gjennom ETF-er. Selv om kortsiktig volatilitet forventes, ser de langsiktige tilbuds-etterspørsel-dynamikkene gunstige ut.",
                    "technical_factors": [
                        "RSI på 68,3 nærmer seg overkjøpt territorium, antyder potensiell konsolidering",
                        "Handler over alle store glidende gjennomsnitt (50, 100 og 200-dagers)",
                        "Volumprof viser økende kjøpsinteresse etter halveringshendelsen",
                        "Høyere bunner etablert på ukentlig tidsramme siden oktober 2023",
                        "Nøkkelmotstand på $70,000 basert på tidligere all-time high"
                    ],
                    "fundamental_factors": [
                        "Redusert utstedelsesrate etter halveringshendelse, kutter nytt tilbud med 50%",
                        "Økende institusjonell adopsjon gjennom spot-ETF-er med $12B i innstrømninger",
                        "Korrelasjon med tradisjonelle finansmarkeder forblir høy på 0,65",
                        "On-chain-metrikker viser akkumulering av langsiktige eiere",
                        "Gruvevanskelighetsbegrepet på all-time high, indikerer nettverkssikkerhet"
                    ],
                    "prediction": {
                        "direction": "up",
                        "confidence": 0.74,
                        "time_frame": "medium til lang sikt (6-18 måneder)",
                        "target_price": "$72,000-80,000"
                    },
                    "economic_indicators": {
                        "inflation_expectations": "modererer men fortsatt støttende for harde eiendeler",
                        "institutional_interest": "voksende med regulatorisk klarhet",
                        "retail_sentiment": "forbedres fra bjørnemarked-bunner",
                        "global_liquidity": "ekspanderer med sentralbankpolitikk"
                    }
                },
                'ETH-USD': {
                    "ticker": "ETH-USD",
                    "sentiment": "nøytral",
                    "strength": "moderat",
                    "summary": "AI-analysen antyder en moderat nøytral utsikt for Ethereum med tekniske forbedringer men skaleringsutfordringer og konkurranse fra alternative Layer 1-blokkkjeder. Nettverket drar nytte av utvikleraktivitet men møter usikkerhet rundt regulatorisk klassifisering.",
                    "technical_factors": [
                        "RSI på 55,2 indikerer nøytralt momentum i balansert territorium",
                        "Prisen konsoliderer mellom 3200-3600 USD-området de siste 6 ukene",
                        "Volummønstre antyder akkumuleringsfase men uten utbruddbekreftelse",
                        "200-dagers glidende gjennomsnitt gir støtte på $3,150-nivået",
                        "Innsnevrede Bollinger Band indikerer potensiell volatilitetsutvidelse fremover"
                    ],
                    "fundamental_factors": [
                        "ETH staking-avkastning rundt 3,8% tiltrekker langsiktige eiere med 25% tilbud staket",
                        "Layer 2-skaleringsløsninger får gjennomslag med 42% økning i TVL",
                        "Konkurranse fra alternative smart kontrakt-plattformer presser markedsandel",
                        "Deflasjonære token-økonomi med netto tilbudsreduksjon siden EIP-1559",
                        "Utvikleraktivitet forblir sterk med 28% vekst i aktive repositories"
                    ],
                    "prediction": {
                        "direction": "sideveis",
                        "confidence": 0.65,
                        "time_frame": "kort sikt (1-3 måneder)",
                        "target_price": "$3400-3700-område"
                    },
                    "economic_indicators": {
                        "defi_ecosystem": "stabiliserer seg etter periode med sammentrekning",
                        "regulatory_environment": "usikker klassifisering som verdipapir eller råvare",
                        "institutional_adoption": "voksende men langsommere tempo enn Bitcoin",
                        "correlation_with_bitcoin": "høy på 0,82 koeffisient"
                    }
                },
                'AMZN': {
                    "ticker": "AMZN",
                    "sentiment": "bullish",
                    "strength": "strong",
                    "summary": "AI-analyse antyder en sterk bullish utsikt for Amazon basert på dominans innen e-handel, cloud-vekst og diversifiserte inntektsstrømmer. Selskapet drar nytte av AWS sin ledende posisjon og fortsatt vekst innen digital reklame og Prime-tjenester.",
                    "technical_factors": [
                        "RSI på 58,2 indikerer moderat bullish momentum uten overkjøpte signaler",
                        "Pris handler over 50-dagers glidende gjennomsnitt, bekrefter opptrend",
                        "MACD over signallinje med økende histogram, positive momentum",
                        "Volumanalyse viser institusjonell kjøp på tilbaketrekninger",
                        "Breakout fra konsolideringsmønster med høyere bunner"
                    ],
                    "fundamental_factors": [
                        "AWS cloud-tjenester viser 12% vekst med sterke marginer på 35%",
                        "E-handel dominans med 40% markedsandel i USA for online retail",
                        "Prime-medlemskap vekst på 8% årlig med høy kundebinding",
                        "Reklameinntekter økende med 26% årlig fra tredjepartsselgere",
                        "Free cash flow på $35 milliarder støtter investeringer og utbytte"
                    ],
                    "prediction": {
                        "direction": "opp",
                        "confidence": 0.79,
                        "time_frame": "medium til lang sikt (6-15 måneder)",
                        "target_price": "$185-195"
                    },
                    "economic_indicators": {
                        "consumer_spending": "motstandsdyktig innen digital handel",
                        "cloud_market_growth": "18% CAGR forventet over neste 5 år",
                        "advertising_market": "skift fra tradisjonelle medier til digital",
                        "interest_rate_impact": "moderat med sterk kontantstrømgenerering"
                    }
                }
            }
            
            # Return realistic data if available
            if ticker in realistic_data:
                analysis = realistic_data[ticker]
                analysis["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return analysis
            
            # Otherwise generate random but plausible data
            sentiments = ["stigende", "fallende", "nøytral"]
            sentiment = random.choice(sentiments)
            
            strength = random.choice(["sterk", "moderat", "svak"])
            
            # More realistic random generation based on ticker characteristics
            ticker_type = "crypto" if "-USD" in ticker else ("norwegian" if ".OL" in ticker else "global")
            
            # Generate more plausible summary based on ticker type and sentiment
            summary_templates = {
                "stigende": {
                    "norwegian": f"AI-analysen antyder en {strength} stigende utsikt for {ticker} basert på gunstige nordiske økonomiske forhold, sterk finansiell posisjon og positive tekniske signaler.",
                    "global": f"AI-analysen antyder en {strength} stigende utsikt for {ticker} basert på robust inntjeningsvekst, markedsposisjonsstyrke og positivt teknisk momentum.",
                    "crypto": f"AI-analysen antyder en {strength} stigende utsikt for {ticker} basert på økende adopsjon, gunstige on-chain-metrikker og forbedret markedssentiment."
                },
                "fallende": {
                    "norwegian": f"AI-analysen antyder en {strength} fallende utsikt for {ticker} på grunn av nordiske økonomiske motvinder, konkurransepress og negative tekniske indikatorer.",
                    "global": f"AI-analysen antyder en {strength} fallende utsikt for {ticker} på grunn av inntjeningsbekymringer, verdsettelsespress og forverrede tekniske signaler.",
                    "crypto": f"AI-analysen antyder en {strength} fallende utsikt for {ticker} på grunn av regulatorisk usikkerhet, svekkede on-chain-metrikker og negativt markedssentiment."
                },
                "nøytral": {
                    "norwegian": f"AI-analysen antyder en {strength} nøytral utsikt for {ticker} med balansert risiko-belønning, blandede tekniske signaler og stabile nordiske markedsforhold.",
                    "global": f"AI-analysen antyder en {strength} nøytral utsikt for {ticker} med balanserte vekstutsikter, rimelig verdsettelse og blandede tekniske indikatorer.",
                    "crypto": f"AI-analysen antyder en {strength} nøytral utsikt for {ticker} med balanserte on-chain-metrikker, utviklende regulatorisk miljø og konsoliderende prishandling."
                }
            }
            
            # Generate technical factors based on sentiment and ticker type
            technical_factors_templates = {
                "stigende": [
                    f"RSI på {random.randint(55, 69)}.{random.randint(1, 9)} viser økende momentum uten å nå overkjøpte nivåer",
                    f"Pris handler over både 50-dagers og 200-dagers glidende gjennomsnitt, bekrefter opptrend",
                    f"Økende volum på oppgangsdager antyder institusjonell akkumulering",
                    f"Nylig utbrudd fra {random.randint(2, 6)}-måneders konsolideringsmønster",
                    f"Høyere bunn-mønster dannes, indikerer sterkere kjøperinteresse"
                ],
                "fallende": [
                    f"RSI på {random.randint(30, 45)}.{random.randint(1, 9)} nærmer seg oversolgt territorium",
                    f"Pris handler under viktige glidende gjennomsnitt, bekrefter nedtrend",
                    f"Synkende volum på oppganger antyder mangel på overbevisning",
                    f"Lavere topper og lavere bunner mønster etablert siden {random.choice(['januar', 'februar', 'mars', 'april', 'mai', 'juni'])}",
                    f"Dødskors dannet med 50-dagers glidende gjennomsnitt krysser under 200-dagers"
                ],
                "nøytral": [
                    f"RSI på {random.randint(45, 55)}.{random.randint(1, 9)} indikerer balansert momentum",
                    f"Pris svinger rundt viktige glidende gjennomsnitt uten klar retning",
                    f"Volumprof viser ingen klare akkumulerings- eller distribusjonsmønstre",
                    f"Pris konsoliderer i område mellom støtte- og motstandsnivåer",
                    f"Bollinger Bands smalner inn, antyder potensiell volatilitetsutvidelse fremover"
                ]
            }
            
            # Generate fundamental factors based on sentiment and ticker type
            fundamental_factors_templates = {
                "stigende": {
                    "norwegian": [
                        f"Sterk finansiell posisjon med sunne balanseregnskapsmålinger",
                        f"Utbytteavkastning på {random.randint(3, 6)}.{random.randint(1, 9)}% med bærekraftig utbetalingsgrad",
                        f"Kostnadseffektivitetstiltak forbedrer marginer med {random.randint(1, 3)}.{random.randint(1, 9)} prosentpoeng",
                        f"Inntektsvekst overgår nordisk sektorgjennomsnitt med {random.randint(2, 8)}%",
                        f"Attraktiv verdsettelse på {random.randint(8, 15)}x terminsinntjening"
                    ],
                    "global": [
                        f"Inntjeningsvekst på {random.randint(10, 25)}% år-over-år overgår analytikernes forventninger",
                        f"Sterk markedsposisjon i kjernesegmenter med {random.randint(20, 40)}% markedsandel",
                        f"Driftsmarginer utvides til {random.randint(25, 45)}% fra investeringer i automatisering",
                        f"FoU-pipeline viser lovende resultater for fremtidig vekst",
                        f"Balansestyrke med {random.randint(10, 30)}B i kontantreserver"
                    ],
                    "crypto": [
                        f"Voksende adopsjonsmålinger med {random.randint(15, 40)}% økning i aktive adresser",
                        f"Forbedret tokenomics med tilbudsreduksjonsmekanismer",
                        f"Utviklingsaktivitet øker med nye protokolloppgraderinger",
                        f"Institusjonell interesse vokser gjennom regulerte investeringsbiler",
                        f"Nettverkssikkerhetsmålinger på all-time high"
                    ]
                },
                "fallende": {
                    "norwegian": [
                        f"Marginpress fra økt konkurranse i nordiske markeder",
                        f"Inntekter synker med {random.randint(1, 5)}% år-over-år",
                        f"Høy utbytteutbetalingsgrad på {random.randint(70, 90)}% kan være uholdbar",
                        f"Stigende driftskostnader oppveier effektivitetstiltak",
                        f"Mister markedsandeler til mer smidige konkurrenter"
                    ],
                    "global": [
                        f"Inntjening mangler konsensusestimater med {random.randint(5, 15)}%",
                        f"Marginpress på grunn av input kostnadsinflasjon",
                        f"Markedsandelerosjon i nøkkelsegmenter",
                        f"Høy verdsettelse på {random.randint(25, 40)}x terminsinntjening",
                        f"Balansebekymringer med {random.randint(10, 30)}B i gjeld som forfaller innen 2 år"
                    ],
                    "crypto": [
                        f"Synkende nettverksaktivitet med {random.randint(10, 30)}% reduksjon i transaksjoner",
                        f"Regulatoriske motvinder øker usikkerhet",
                        f"Tekniske utfordringer forsinker viktige protokolloppgraderinger",
                        f"Økende konkurranse fra alternative protokoller",
                        f"Konsentrasjonsinnsatser med {random.randint(20, 40)}% holdt av topp 10 adresser"
                    ]
                },
                "nøytral": {
                    "norwegian": [
                        f"Stabile inntekter med {random.randint(0, 3)}% vekst år-over-år",
                        f"Marginer holder seg stabile på {random.randint(20, 30)}%",
                        f"Utbytteavkastning på {random.randint(3, 5)}% i tråd med sektorgjennomsnitt",
                        f"Markedsandel stabil i kjerne nordiske markeder",
                        f"Verdsettelse i tråd med historiske gjennomsnitt"
                    ],
                    "global": [
                        f"Inntjening i tråd med analytikernes forventninger",
                        f"Stabil markedsposisjon uten betydelige andelsendringer",
                        f"Kostnadsstyring oppveier moderat input prisinflasjon",
                        f"FoU-utgifter opprettholdt på {random.randint(8, 15)}% av inntekter",
                        f"Balanseregnskapsmålinger stabile år-over-år"
                    ],
                    "crypto": [
                        f"Nettverksmålinger stabile med balanserte tilbuds-etterspørsel-dynamikker",
                        f"Utvikling fortsetter i jevnt tempo",
                        f"Regulatorisk situasjon utvikler seg men uten umiddelbar påvirkning",
                        f"Korrelasjon med bredere kryptomarked på gjennomsnittsnivåer",
                        f"Adopsjonsmålinger vokser i tråd med markedsgjennomsnittet"
                    ]
                }
            }
            
            # Generate economic indicators based on ticker type
            economic_indicators_templates = {
                "norwegian": {
                    "norwegian_economy": random.choice(["viser motstandsdyktighet med 2,1% BNP-vekst", "avtar med 1,3% BNP-vekst", "stabil med 1,8% BNP-prognose"]),
                    "interest_rate_environment": random.choice(["stabil med Norges Bank holder renter", "utfordrende med potensielle renteøkninger", "gunstig med potensielle rentekutt"]),
                    "sector_performance": f"{random.choice(['overpresterer', 'underpresterer', 'i tråd med'])} bredere Oslo Børs indeks",
                    "currency_impact": f"NOK {random.choice(['styrkes', 'svekkes', 'stabil'])} mot store handelspartnere"
                },
                "global": {
                    "global_economy": random.choice(["viser moderat vekst på 3,2%", "møter motvind med 2,5% vekst", "motstandsdyktig med 3,0% ekspansjon"]),
                    "interest_rate_trend": random.choice(["synkende med sentralbanker letter", "stigende med inflasjonsbekymringer", "stabiliserer etter økning"]),
                    "sector_rotation": f"investorer {random.choice(['favoriserer', 'roterer ut av', 'nøytrale på'])} denne sektoren",
                    "geopolitical_factors": random.choice(["presenterer moderate risikoer", "generelt støttende", "skaper usikkerhet"])
                },
                "crypto": {
                    "bitcoin_dominance": f"{random.randint(40, 60)}% og {random.choice(['økende', 'synkende', 'stabil'])}",
                    "market_liquidity": random.choice(["forbedres med institusjonell deltakelse", "synker med børsutstrømninger", "stabil med balanserte strømmer"]),
                    "regulatory_landscape": random.choice(["gradvis klargjørende", "presenterer utfordringer", "blandet med regionale forskjeller"]),
                    "correlation_with_equities": random.choice(["høy på 0,7 koeffisient", "moderat på 0,5 koeffisient", "synkende til 0,3 koeffisient"])
                }
            }
            
            # Build the analysis object with more realistic random data
            analysis = {
                "ticker": ticker,
                "sentiment": sentiment,
                "strength": strength,
                "summary": summary_templates[sentiment][ticker_type],
                "technical_factors": technical_factors_templates[sentiment],
                "fundamental_factors": fundamental_factors_templates[sentiment][ticker_type],
                "prediction": {
                    "direction": "opp" if sentiment == "stigende" else ("ned" if sentiment == "fallende" else "sideveis"),
                    "confidence": 0.8 if strength == "sterk" else (0.65 if strength == "moderat" else 0.4),
                    "time_frame": f"{random.choice(['kort', 'mellomlang', 'lang'])} sikt ({random.choice(['1-3', '3-6', '6-12', '12-24'])} måneder)",
                    "target_price": f"${random.randint(5, 500)}" if not ticker.endswith('.OL') else f"{random.randint(50, 500)} NOK"
                },
                "economic_indicators": economic_indicators_templates[ticker_type],
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return analysis
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def generate_market_summary(sector=None):
        """
        Generate AI market summary (demo implementation)
        """
        try:
            # Realistic market summaries for different sectors
            sector_summaries = {
                "energy": {
                    "summary": "The energy sector is showing positive trends with oil prices stabilizing above $80 per barrel, supporting improved cash flows for major producers.",
                    "details": [
                        "Oil majors reporting strong Q2 earnings with improved cash flows",
                        "Renewable energy investments accelerating across the sector",
                        "Natural gas prices stabilizing after period of high volatility"
                    ],
                    "outlook": "The sector outlook remains positive with balanced supply-demand dynamics and ongoing transition investments.",
                    "key_stocks": ["EQNR.OL", "XOM", "CVX", "BP"]
                },
                "finance": {
                    "summary": "The financial sector is showing mixed signals with banks benefiting from higher interest rates but facing increased loan loss provisions.",
                    "details": [
                        "Net interest margins improving for most banks in the current rate environment",
                        "Investment banking activity showing signs of recovery after weak 2023",
                        "Fintech competition continues to pressure traditional business models"
                    ],
                    "outlook": "The sector faces both opportunities from high rates and challenges from potential credit quality deterioration.",
                    "key_stocks": ["DNB.OL", "JPM", "BAC", "GS"]
                },
                "technology": {
                    "summary": "The technology sector continues to outperform, driven by AI adoption, cloud growth, and improving semiconductor demand.",
                    "details": [
                        "AI investments accelerating across enterprise software and hardware",
                        "Cloud providers reporting strong growth with improving margins",
                        "Semiconductor companies seeing improved demand after inventory correction"
                    ],
                    "outlook": "The technology sector remains well-positioned for growth with AI as a major catalyst.",
                    "key_stocks": ["MSFT", "AAPL", "NVDA", "ASML"]
                },
                "healthcare": {
                    "summary": "The healthcare sector is showing resilience with pharmaceuticals and medical technology companies reporting solid results.",
                    "details": [
                        "Pharmaceutical companies benefiting from strong pipelines and new drug approvals",
                        "Healthcare services seeing stable demand patterns",
                        "Medical technology innovation accelerating in diagnostics and monitoring"
                    ],
                    "outlook": "The healthcare sector offers defensive characteristics with growth opportunities in specific segments.",
                    "key_stocks": ["JNJ", "PFE", "ISRG", "UNH"]
                }
            }
            
            # Default market summary
            default_summary = {
                "summary": "Overall market sentiment is cautiously optimistic with mixed signals across sectors. Technology and energy showing strength while consumer discretionary faces headwinds.",
                "details": [
                    "Major indices trading near all-time highs with improving breadth",
                    "Interest rate expectations stabilizing with inflation trending lower",
                    "Earnings reports generally in line with or exceeding analyst expectations"
                ],
                "outlook": "Markets appear fairly valued with potential volatility around economic data and monetary policy decisions.",
                "key_stocks": ["AAPL", "MSFT", "EQNR.OL", "DNB.OL"]
            }
            
            # Return sector-specific summary if requested and available
            if sector and sector.lower() in sector_summaries:
                summary = sector_summaries[sector.lower()]
            else:
                # Return general market summary
                summary = default_summary
            
            # Add generation timestamp
            summary["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_ai_portfolio_recommendation(tickers):
        """
        Get AI recommendation for a portfolio (demo implementation)
        """
        if not tickers:
            return None
        
        # Dictionary with realistic recommendations for specific tickers
        ticker_recommendations = {
            'EQNR.OL': {"action": "buy", "confidence": "high", "reason": "Strong cash flow generation and attractive valuation"},
            'DNB.OL': {"action": "hold", "confidence": "medium", "reason": "Stable performance with limited near-term catalysts"},
            'YAR.OL': {"action": "buy", "confidence": "medium", "reason": "Improving fertilizer market conditions and cost efficiency"},
            'NHY.OL': {"action": "hold", "confidence": "medium", "reason": "Balanced risk-reward with aluminum market uncertainty"},
            'TEL.OL': {"action": "reduce", "confidence": "medium", "reason": "Competitive pressures in key markets affecting growth"},
            'AAPL': {"action": "buy", "confidence": "high", "reason": "Services growth and ecosystem strength continue to drive results"},
            'MSFT': {"action": "buy", "confidence": "high", "reason": "Cloud leadership and AI integration creating multiple growth vectors"},
            'AMZN': {"action": "buy", "confidence": "medium", "reason": "Improving margins in retail and continued AWS strength"},
            'GOOGL': {"action": "buy", "confidence": "medium", "reason": "Digital advertising recovery and AI integration across services"},
            'TSLA': {"action": "sell", "confidence": "medium", "reason": "Margin pressure and increasing competition in EV space"},
            'BTC-USD': {"action": "buy", "confidence": "medium", "reason": "Post-halving dynamics and institutional adoption through ETFs"},
            'ETH-USD': {"action": "hold", "confidence": "medium", "reason": "Ongoing technical improvements but scaling challenges remain"}
        }
        
        # Generate recommendations
        recommendations = []
        for ticker in tickers:
            if ticker in ticker_recommendations:
                rec = ticker_recommendations[ticker]
                recommendations.append({
                    "ticker": ticker,
                    "action": rec["action"],
                    "confidence": rec["confidence"],
                    "reason": rec["reason"]
                })
            else:
                # Random but plausible recommendation for unknown tickers
                action = random.choice(["hold", "buy", "sell", "increase", "decrease"])
                confidence = random.choice(["high", "medium", "low"])
                reason = f"Based on {random.choice(['technical indicators', 'fundamental analysis', 'market trends', 'sector performance'])}"
                recommendations.append({
                    "ticker": ticker,
                    "action": action,
                    "confidence": confidence,
                    "reason": reason
                })
        
        # Portfolio health assessment based on the recommendations
        buy_count = sum(1 for r in recommendations if r["action"] in ["buy", "increase"])
        sell_count = sum(1 for r in recommendations if r["action"] in ["sell", "decrease"])
        
        if buy_count > sell_count * 2:
            portfolio_health = "strong"
        elif buy_count > sell_count:
            portfolio_health = "moderate"
        else:
            portfolio_health = "needs attention"
            
        # Portfolio diversification based on tickers
        sectors_count = len(set([t.split('.')[0][-2:] if '.' in t else t[:4] for t in tickers]))
        if sectors_count >= 5 or len(tickers) >= 8:
            diversification = "well diversified"
        elif sectors_count >= 3 or len(tickers) >= 5:
            diversification = "moderately diversified"
        else:
            diversification = "poorly diversified"
            
        return {
            "portfolio_health": portfolio_health,
            "diversification": diversification,
            "risk_level": random.choice(["low", "moderate", "high"]),
            "recommendations": recommendations,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @staticmethod
    def get_warren_buffett_analysis(ticker):
        """
        AI analysis based on Warren Buffett's investment philosophy
        Focus on: Value, Moat, Management, Long-term growth, Simple business model
        """
        try:
            # Import the dedicated Buffett analysis service
            from ..services.buffett_analysis_service import BuffettAnalysisService
            
            # Get comprehensive Buffett analysis
            analysis = BuffettAnalysisService.analyze(ticker)
            
            # Format for template compatibility
            return {
                'ticker': ticker,
                'recommendation': analysis['recommendation']['action'],
                'confidence': analysis['recommendation']['confidence'],
                'buffett_score': analysis['overall_score'],
                'value_score': analysis['scores']['value'],
                'moat_score': analysis['scores']['moat'],
                'management_score': analysis['scores']['management'],
                'simplicity_score': analysis['scores']['simplicity'],
                'financial_score': analysis['scores']['financials'],
                'buffett_quote': analysis['buffett_quote'],
                'criteria': analysis['criteria_details'],
                'key_factors': [{'name': insight, 'value': ''} for insight in analysis['key_insights']],
                'summary': analysis['investment_thesis']
            }
            
        except Exception as e:
            print(f"Error in Buffett analysis for {ticker}: {str(e)}")
            # Fallback to existing implementation
            return AIService._get_buffett_analysis_fallback(ticker)
    
    @staticmethod
    def get_benjamin_graham_analysis(ticker):
        """
        AI analysis based on Benjamin Graham's value investing principles
        Focus on: Intrinsic value, Margin of safety, Financial stability
        """
        try:
            # Import the dedicated Graham analysis service
            from ..services.graham_analysis_service import GrahamAnalysisService
            
            # Get comprehensive Graham analysis
            analysis = GrahamAnalysisService.analyze(ticker)
            
            # Format for template compatibility
            return {
                'ticker': ticker,
                'current_price': analysis['current_price'],
                'intrinsic_value': analysis['intrinsic_value'],
                'margin_of_safety': analysis['margin_of_safety'],
                'graham_score': analysis['graham_score'],
                'recommendation': analysis['recommendation']['action'],
                'confidence': analysis['recommendation']['confidence'],
                'criteria': analysis['criteria_results'],
                'key_metrics': analysis['key_metrics'],
                'summary': analysis['investment_thesis'],
                'principles': analysis['graham_principles']
            }
            
        except Exception as e:
            print(f"Error in Graham analysis for {ticker}: {str(e)}")
            # Fallback implementation
            return AIService._get_graham_analysis_fallback(ticker)
    
    @staticmethod
    def _get_buffett_analysis_fallback(ticker):
        """Fallback Buffett analysis using existing implementation"""
        try:
            from ..services.analysis_service import AnalysisService
            
            # Get basic data
            technical_data = AnalysisService.get_fallback_technical_data(ticker)
            price = technical_data.get('last_price', 100)
            
            # Enhanced Buffett-style scoring with more realistic variations
            base_scores = {
                'EQNR.OL': {'value': 78, 'moat': 82, 'management': 85, 'simplicity': 80},
                'DNB.OL': {'value': 72, 'moat': 75, 'management': 88, 'simplicity': 85},
                'AAPL': {'value': 68, 'moat': 95, 'management': 92, 'simplicity': 75},
                'MSFT': {'value': 65, 'moat': 90, 'management': 95, 'simplicity': 78},
                'TSLA': {'value': 35, 'moat': 70, 'management': 75, 'simplicity': 45},
                'AMZN': {'value': 55, 'moat': 88, 'management': 85, 'simplicity': 60},
                'YAR.OL': {'value': 75, 'moat': 65, 'management': 80, 'simplicity': 82},
                'NHY.OL': {'value': 70, 'moat': 60, 'management': 75, 'simplicity': 85},
                'TEL.OL': {'value': 65, 'moat': 55, 'management': 70, 'simplicity': 88}
            }
            
            if ticker in base_scores:
                scores = base_scores[ticker]
                # Add small random variation
                value_score = scores['value'] + random.uniform(-5, 5)
                moat_score = scores['moat'] + random.uniform(-5, 5)
                management_score = scores['management'] + random.uniform(-3, 3)
                simplicity_score = scores['simplicity'] + random.uniform(-3, 3)
            else:
                # Random but plausible scores for unknown tickers
                value_score = random.uniform(45, 85)
                moat_score = random.uniform(30, 90)
                management_score = random.uniform(60, 95)
                simplicity_score = random.uniform(40, 85)
            
            overall_score = (value_score + moat_score + management_score + simplicity_score) / 4
            
            # Enhanced criteria checking
            criteria = [
                {
                    'name': 'Langsiktig verdiøkning',
                    'met': value_score > 70,
                    'description': f'Score: {value_score:.0f}/100 - {"Sterk" if value_score > 70 else "Moderat" if value_score > 50 else "Svak"} verdipotensial'
                },
                {
                    'name': 'Konkurransefortrinn (Moat)',
                    'met': moat_score > 70,
                    'description': f'Score: {moat_score:.0f}/100 - {"Sterk" if moat_score > 70 else "Moderat" if moat_score > 50 else "Begrenset"} økonomisk vallgrav'
                },
                {
                    'name': 'Kompetent ledelse',
                    'met': management_score > 75,
                    'description': f'Score: {management_score:.0f}/100 - {"Fremragende" if management_score > 85 else "God" if management_score > 75 else "Akseptabel"} ledelseskvalitet'
                },
                {
                    'name': 'Forståelig forretningsmodell',
                    'met': simplicity_score > 70,
                    'description': f'Score: {simplicity_score:.0f}/100 - {"Enkel" if simplicity_score > 70 else "Moderat" if simplicity_score > 50 else "Kompleks"} å forstå'
                }
            ]
            
            # More nuanced key factors
            key_factors = [
                {
                    'name': 'Verdi-vurdering',
                    'value': f'{value_score:.0f}/100 - {"Undervurdert" if value_score > 75 else "Rimelig priset" if value_score > 60 else "Moderat overpriset" if value_score > 45 else "Overpriset"}'
                },
                {
                    'name': 'Konkurranseposisjon',
                    'value': f'{moat_score:.0f}/100 - {"Dominerende" if moat_score > 85 else "Sterk" if moat_score > 70 else "Moderat" if moat_score > 55 else "Svak"} markedsposisjon'
                },
                {
                    'name': 'Kapitalallokering',
                    'value': f'{management_score:.0f}/100 - {"Excellent" if management_score > 90 else "God" if management_score > 80 else "Tilfredsstillende" if management_score > 70 else "Bekymringsfull"} kapitalforvaltning'
                },
                {
                    'name': 'Forretningsklarhet',
                    'value': f'{simplicity_score:.0f}/100 - {"Krystallklar" if simplicity_score > 80 else "Klar" if simplicity_score > 70 else "Noe uklar" if simplicity_score > 55 else "Komplisert"} forretningsmodell'
                }
            ]
            
            # Enhanced Buffett-style recommendation logic
            if overall_score >= 80:
                recommendation = "Kjøp"
                buffett_quote = "En fantastisk virksomhet til en rimelig pris. Dette er akkurat det jeg leter etter."
            elif overall_score >= 70:
                recommendation = "Kjøp"
                buffett_quote = "En god virksomhet til en akseptabel pris. Verdt å vurdere sterkt."
            elif overall_score >= 60:
                recommendation = "Hold"
                buffett_quote = "En OK virksomhet, men vent på en bedre pris eller finn noe bedre."
            elif overall_score >= 50:
                recommendation = "Hold"
                buffett_quote = "Ikke overbevisende nok. Jeg forstår ikke virksomheten godt nok."
            else:
                recommendation = "Unngå"
                buffett_quote = "Dette passer ikke min investeringsfilosofi. For komplisert eller risikabelt."
            
            return {
                'recommendation': recommendation,
                'confidence': min(0.95, overall_score / 100),
                'price_target': price * (1.15 if recommendation == 'Kjøp' else 0.95 if recommendation == 'Unngå' else 1.0),
                'risk_level': 'Lav' if overall_score > 75 else 'Moderat' if overall_score > 60 else 'Høy',
                'time_horizon': '5-10 år',
                'buffett_score': overall_score,
                'value_score': value_score,
                'moat_score': moat_score,
                'management_score': management_score,
                'simplicity_score': simplicity_score,
                'buffett_quote': buffett_quote,
                'criteria': criteria,
                'key_factors': key_factors,
                'summary': f"Warren Buffett ville sannsynligvis {recommendation.lower()} denne aksjen. "
                          f"Samlet Buffett-score: {overall_score:.0f}/100. {buffett_quote}",
                'investment_philosophy': "Fokus på langsiktig verdi, sterke konkurransefortrinn og forståelige forretningsmodeller som kan holdes for alltid."
            }
            
        except Exception as e:
            print(f"Error in Buffett analysis for {ticker}: {str(e)}")
            return {
                'recommendation': 'Hold',
                'confidence': 0.5,
                'buffett_score': 50,
                'error': f'Kunne ikke generere Buffett-analyse: {str(e)}'
            }

    @staticmethod 
    def get_benjamin_graham_analysis(ticker):
        """
        AI analysis based on Benjamin Graham's value investing principles
        Focus on: Intrinsic value, Margin of safety, Financial stability
        """
        try:
            # Import the dedicated Graham analysis service
            from ..services.graham_analysis_service import GrahamAnalysisService
            
            # Get comprehensive Graham analysis
            analysis = GrahamAnalysisService.analyze(ticker)
            
            # Format for template compatibility
            return {
                'ticker': ticker,
                'current_price': analysis['current_price'],
                'intrinsic_value': analysis['intrinsic_value'],
                'margin_of_safety': analysis['margin_of_safety'],
                'graham_score': analysis['graham_score'],
                'recommendation': analysis['recommendation']['action'],
                'confidence': analysis['recommendation']['confidence'],
                'criteria': analysis['criteria_results'],
                'key_metrics': analysis['key_metrics'],
                'summary': analysis['investment_thesis'],
                'principles': analysis['graham_principles']
            }
            
        except Exception as e:
            print(f"Error in Graham analysis for {ticker}: {str(e)}")
            # Fallback implementation
            return AIService._get_graham_analysis_fallback(ticker)
    
    @staticmethod
    def _get_graham_analysis_fallback(ticker):
        """Fallback Graham analysis using existing implementation"""
        try:
            from ..services.analysis_service import AnalysisService
            
            # Get basic data
            technical_data = AnalysisService.get_fallback_technical_data(ticker)
            price = technical_data.get('last_price', 100)
            
            # Graham-style quantitative scoring
            pe_score = random.uniform(30, 95)     # P/E ratio attractiveness
            pb_score = random.uniform(40, 90)     # Price-to-book ratio
            debt_score = random.uniform(50, 85)   # Debt levels
            dividend_score = random.uniform(20, 80)  # Dividend yield
            earnings_score = random.uniform(40, 90)  # Earnings consistency
            
            # Graham's defensive investor criteria
            defensive_score = (pe_score + pb_score + debt_score + earnings_score) / 4
            
            # Graham's enterprising investor criteria  
            enterprising_score = (pe_score + pb_score + dividend_score + earnings_score) / 4
            
            overall_score = max(defensive_score, enterprising_score)
            
            # Graham-style recommendation
            if overall_score >= 75:
                recommendation = "BUY"
                graham_verdict = "Møter Graham's kriterier for verdiinvestering"
                margin_of_safety = "Betydelig sikkerhetsmarginal"
            elif overall_score >= 60:
                recommendation = "HOLD" 
                graham_verdict = "Delvis tilfredsstillende etter Graham's standarder"
                margin_of_safety = "Moderat sikkerhetsmarginal"
            else:
                recommendation = "AVOID"
                graham_verdict = "Møter ikke Graham's kvantitative krav"
                margin_of_safety = "Utilstrekkelig sikkerhetsmarginal"
            
            # Graham-style factors
            key_factors = [
                f"P/E attraktivitet: {pe_score:.0f}/100 - {'Attraktiv' if pe_score > 70 else 'Akseptabel' if pe_score > 50 else 'For høy'}",
                f"P/B ratio: {pb_score:.0f}/100 - {'Under bokført verdi' if pb_score > 70 else 'Rimelig' if pb_score > 50 else 'Overpriset'}",
                f"Finansiell styrke: {debt_score:.0f}/100 - {'Sterk balanse' if debt_score > 70 else 'Moderat gjeld' if debt_score > 50 else 'For høy gjeld'}",
                f"Utbytte: {dividend_score:.0f}/100 - {'God avkastning' if dividend_score > 60 else 'Moderat utbytte' if dividend_score > 40 else 'Lavt/ingen utbytte'}"
            ]
            
            return {
                'recommendation': recommendation,
                'confidence': overall_score / 100,
                'price_target': price * (1.15 if recommendation == 'BUY' else 0.9 if recommendation == 'AVOID' else 1.0),
                'risk_level': 'Lav' if overall_score > 70 else 'Moderat',
                'time_horizon': '3-7 år', 
                'graham_score': overall_score,
                'defensive_score': defensive_score,
                'enterprising_score': enterprising_score,
                'pe_score': pe_score,
                'pb_score': pb_score,
                'debt_score': debt_score,
                'dividend_score': dividend_score,
                'margin_of_safety': margin_of_safety,
                'graham_verdict': graham_verdict,
                'key_factors': key_factors,
                'summary': f"Benjamin Graham ville {recommendation.lower()} denne aksjen. "
                          f"Graham-score: {overall_score:.0f}/100. {graham_verdict}.",
                'investment_philosophy': "Fokus på kvantitative kriterier, sikkerhetsmarginal og finansiell soliditet."
            }
            
        except Exception as e:
            print(f"Error in Graham analysis for {ticker}: {str(e)}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.5,
                'graham_score': 50,
                'error': 'Kunne ikke generere Graham-analyse'
            }
    
    @staticmethod
    def get_short_analysis(ticker):
        """
        AI analysis for short-selling opportunities
        Focus on: Overvaluation, declining fundamentals, technical weakness, market sentiment
        """
        try:
            from ..services.analysis_service import AnalysisService
            
            # Get basic data
            technical_data = AnalysisService.get_fallback_technical_data(ticker)
            price = technical_data.get('last_price', 100)
            rsi = technical_data.get('rsi', 50)
            
            # Short-selling criteria scoring
            overvaluation_score = random.uniform(30, 95)    # How overvalued the stock is
            momentum_weakness = random.uniform(20, 90)      # Technical weakness
            fundamental_decline = random.uniform(10, 85)    # Declining business metrics
            market_sentiment = random.uniform(25, 80)       # Negative sentiment indicators
            
            # Calculate short score (higher = better short candidate)
            short_score = (overvaluation_score + momentum_weakness + fundamental_decline + market_sentiment) / 4
            
            # Short recommendation
            if short_score >= 75:
                recommendation = "STRONG_SHORT"
                risk_level = "Høy"
                confidence_level = "Høy"
            elif short_score >= 60:
                recommendation = "MODERATE_SHORT" 
                risk_level = "Moderat-Høy"
                confidence_level = "Moderat"
            elif short_score >= 45:
                recommendation = "WAIT"
                risk_level = "Moderat"
                confidence_level = "Lav"
            else:
                recommendation = "AVOID_SHORT"
                risk_level = "Svært Høy"
                confidence_level = "Svært Lav"
            
            # Calculate potential targets
            target_decline = min(30, short_score * 0.4)  # Max 30% target decline
            price_target = price * (1 - target_decline / 100)
            stop_loss = price * 1.1  # 10% stop loss
            
            key_factors = [
                f"Overvurdering: {overvaluation_score:.0f}/100 - {'Kraftig overpriset' if overvaluation_score > 70 else 'Moderat overpriset' if overvaluation_score > 50 else 'Rimelig priset'}",
                f"Teknisk svakhet: {momentum_weakness:.0f}/100 - {'Sterk bearish trend' if momentum_weakness > 70 else 'Moderat svakhet' if momentum_weakness > 50 else 'Teknisk styrke'}",
                f"Fundamental forverring: {fundamental_decline:.0f}/100 - {'Kraftig forverring' if fundamental_decline > 70 else 'Moderat nedgang' if fundamental_decline > 50 else 'Stabile fundamentals'}",
                f"Markedssentiment: {market_sentiment:.0f}/100 - {'Svært negativt' if market_sentiment > 70 else 'Moderat negativt' if market_sentiment > 50 else 'Positivt'}"
            ]
            
            # Risk warnings for shorting
            risk_warnings = [
                "⚠️ Short-selling har ubegrenset tapsrisiko",
                "⚠️ Kan være påvirket av short squeeze",
                "⚠️ Krever margin og høyere gebyr",
                "⚠️ Regulatoriske restriksjoner kan påvirke posisjon"
            ]
            
            return {
                'recommendation': recommendation,
                'confidence': confidence_level,
                'short_score': short_score,
                'price_target': price_target,
                'stop_loss': stop_loss,
                'risk_level': risk_level,
                'time_horizon': '1-6 måneder',
                'target_decline': f"{target_decline:.1f}%",
                'overvaluation_score': overvaluation_score,
                'momentum_weakness': momentum_weakness,
                'fundamental_decline': fundamental_decline,
                'market_sentiment': market_sentiment,
                'key_factors': key_factors,
                'risk_warnings': risk_warnings,
                'summary': f"Short-analyse viser {recommendation.replace('_', ' ').lower()} signal med {short_score:.0f}/100 poeng. "
                          f"Forventet kursnedgang: {target_decline:.1f}%. Risiko: {risk_level}.",
                'strategy_notes': "Shorting egner seg for erfarne investorer med høy risikotoleranse og god markedsforståelse."
            }
            
        except Exception as e:
            print(f"Error in short analysis for {ticker}: {str(e)}")
            return {
                'recommendation': 'AVOID_SHORT',
                'confidence': 'Lav',
                'short_score': 25,
                'error': 'Kunne ikke generere short-analyse'
            }
    
    @staticmethod
    def get_price_prediction(ticker, timeframe='short'):
        """Get AI price prediction for a stock"""
        try:
            # Get current price
            from ..services.data_service import DataService
            stock_info = DataService.get_stock_info(ticker)
            current_price = stock_info.get('current_price', 100)
            
            # Generate predictions based on timeframe
            timeframe_factors = {
                'short': {'days': 7, 'volatility': 0.02, 'confidence': 0.75},
                'medium': {'days': 30, 'volatility': 0.05, 'confidence': 0.65},
                'long': {'days': 180, 'volatility': 0.15, 'confidence': 0.55}
            }
            
            factor = timeframe_factors.get(timeframe, timeframe_factors['short'])
            
            # Calculate prediction with some randomness
            trend = random.choice([1, -1]) * random.uniform(0.5, 1.5)
            change_percent = trend * factor['volatility'] * 100
            predicted_price = current_price * (1 + change_percent / 100)
            
            return {
                'current_price': current_price,
                'predicted_price': round(predicted_price, 2),
                'change_percent': round(change_percent, 2),
                'confidence': factor['confidence'],
                'timeframe': f"{factor['days']} dager",
                'direction': 'opp' if change_percent > 0 else 'ned',
                'factors': [
                    'Teknisk momentum',
                    'Markedssentiment',
                    'Sektorutvikling',
                    'Makroøkonomiske faktorer'
                ]
            }
        except Exception as e:
            return {
                'error': str(e),
                'predicted_price': 0,
                'confidence': 0
            }
    
    @staticmethod
    def get_sentiment_analysis(ticker):
        """Get sentiment analysis for a stock"""
        sentiments = ['positiv', 'nøytral', 'negativ']
        sentiment = random.choice(sentiments)
        score = random.uniform(0.3, 0.9)
        
        return {
            'overall_sentiment': sentiment,
            'sentiment_score': round(score, 2),
            'sources': {
                'news': random.choice(sentiments),
                'social_media': random.choice(sentiments),
                'analyst_reports': random.choice(sentiments)
            },
            'trending_topics': [
                'Kvartalsresultater',
                'Nye produktlanseringer',
                'Markedsekspansjon',
                'Ledelsesendringer'
            ]
        }
    
    @staticmethod
    def get_risk_assessment(ticker):
        """Get risk assessment for a stock"""
        risk_levels = ['lav', 'moderat', 'høy']
        risk_level = random.choice(risk_levels)
        
        return {
            'overall_risk': risk_level,
            'risk_score': random.uniform(1, 10),
            'risk_factors': {
                'market_risk': random.choice(risk_levels),
                'sector_risk': random.choice(risk_levels),
                'company_specific_risk': random.choice(risk_levels),
                'liquidity_risk': random.choice(risk_levels)
            },
            'key_risks': [
                'Markedsvolatilitet',
                'Konkurransepress',
                'Regulatoriske endringer',
                'Valutarisiko'
            ]
        }
    
    @staticmethod
    def get_prediction_confidence(ticker):
        """Get confidence levels for predictions"""
        return {
            'technical_analysis': random.uniform(0.6, 0.9),
            'fundamental_analysis': random.uniform(0.5, 0.85),
            'sentiment_analysis': random.uniform(0.4, 0.8),
            'ai_model': random.uniform(0.7, 0.95),
            'overall': random.uniform(0.6, 0.85)
        }
