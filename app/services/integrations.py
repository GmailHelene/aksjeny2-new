import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os
from ..services.portfolio_service import get_ai_analysis
import logging

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for handling external integrations like Discord and Slack"""
    
    @staticmethod
    def send_discord_alert(webhook_url: str, title: str, message: str, 
                          color: int = 0x00ff00, fields: list = None) -> bool:
        """Send alert to Discord webhook"""
        try:
            embed = {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Aksjeradar AI",
                    "icon_url": "https://your-domain.com/static/images/logo-32.png"
                }
            }
            
            if fields:
                embed["fields"] = fields
                
            payload = {
                "embeds": [embed],
                "username": "Aksjeradar AI"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    @staticmethod
    def send_slack_alert(webhook_url: str, title: str, message: str, 
                        color: str = "good", fields: list = None) -> bool:
        """Send alert to Slack webhook"""
        try:
            attachment = {
                "color": color,
                "title": title,
                "text": message,
                "footer": "Aksjeradar AI",
                "ts": int(datetime.utcnow().timestamp())
            }
            
            if fields:
                attachment["fields"] = [
                    {"title": field["name"], "value": field["value"], "short": field.get("inline", True)}
                    for field in fields
                ]
            
            payload = {
                "attachments": [attachment],
                "username": "Aksjeradar AI",
                "icon_emoji": ":chart_with_upwards_trend:"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            return False
    
    @staticmethod
    def format_stock_alert(symbol: str, price: float, change_pct: float, 
                          alert_type: str, ai_score: float = None) -> tuple:
        """Format stock alert for external services"""
        emoji = "🚀" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
        color = 0x00ff00 if change_pct > 0 else 0xff0000 if change_pct < 0 else 0xffff00
        slack_color = "good" if change_pct > 0 else "danger" if change_pct < 0 else "warning"
        
        title = f"{emoji} {symbol} - {alert_type}"
        message = f"**Pris:** {price:,.2f} NOK\n**Endring:** {change_pct:+.2f}%"
        
        fields = [
            {"name": "Symbol", "value": symbol, "inline": True},
            {"name": "Pris", "value": f"{price:,.2f} NOK", "inline": True},
            {"name": "Endring", "value": f"{change_pct:+.2f}%", "inline": True}
        ]
        
        if ai_score:
            message += f"\n**AI Score:** {ai_score:.1f}/10"
            fields.append({"name": "AI Score", "value": f"{ai_score:.1f}/10", "inline": True})
        
        return title, message, color, slack_color, fields

class WeeklyReportService:
    """Service for generating and sending weekly AI reports"""
    
    @staticmethod
    def generate_weekly_watchlist_report(user_id: int) -> Dict[str, Any]:
        """Generate comprehensive weekly report for user's watchlist"""
        from ..models.watchlist import Watchlist
        from ..services.ai_service import AIService
        
        try:
            # Get user's watchlist
            watchlist_items = Watchlist.query.filter_by(user_id=user_id).all()
            
            if not watchlist_items:
                return {"error": "Ingen aksjer i watchlist"}
            
            report_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_stocks": len(watchlist_items),
                "performance_summary": {},
                "ai_insights": [],
                "top_performers": [],
                "recommendations": []
            }
            
            # Analyze each stock
            for item in watchlist_items:
                try:
                    # Get AI analysis
                    analysis = get_ai_analysis(item.symbol)
                    
                    stock_data = {
                        "symbol": item.symbol,
                        "current_price": analysis.get("current_price", 0),
                        "week_change": analysis.get("week_change", 0),
                        "ai_score": analysis.get("ai_score", 0),
                        "signals": analysis.get("signals", []),
                        "risk_level": analysis.get("risk_assessment", {}).get("level", "Medium")
                    }
                    
                    report_data["ai_insights"].append(stock_data)
                    
                    # Track top performers
                    if stock_data["week_change"] > 5:
                        report_data["top_performers"].append(stock_data)
                        
                except Exception as e:
                    logger.error(f"Error analyzing {item.symbol}: {e}")
                    continue
            
            # Generate recommendations
            report_data["recommendations"] = WeeklyReportService._generate_recommendations(
                report_data["ai_insights"]
            )
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _generate_recommendations(insights: list) -> list:
        """Generate AI-based recommendations from insights"""
        recommendations = []
        
        # Find high-scoring stocks
        high_scores = [stock for stock in insights if stock.get("ai_score", 0) > 7.5]
        if high_scores:
            recommendations.append({
                "type": "BUY_SIGNAL",
                "title": "Sterke kjøpssignaler",
                "description": f"AI-en anbefaler å vurdere {', '.join([s['symbol'] for s in high_scores[:3]])} basert på høy AI-score.",
                "stocks": [s["symbol"] for s in high_scores[:3]]
            })
        
        # Find underperformers
        low_performers = [stock for stock in insights if stock.get("week_change", 0) < -10]
        if low_performers:
            recommendations.append({
                "type": "RISK_WARNING",
                "title": "Risiko advarsel",
                "description": f"Vær forsiktig med {', '.join([s['symbol'] for s in low_performers[:3]])} - betydelig fall denne uken.",
                "stocks": [s["symbol"] for s in low_performers[:3]]
            })
        
        # Portfolio diversification advice
        sectors = {}
        for stock in insights:
            # Simplified sector detection based on symbol (you might want to enhance this)
            if stock["symbol"].startswith(("EQNR", "AKA")):
                sector = "Energy"
            elif stock["symbol"].startswith(("DNB", "NOR")):
                sector = "Finance"
            else:
                sector = "Technology"
            sectors[sector] = sectors.get(sector, 0) + 1
        
        if len(sectors) < 3:
            recommendations.append({
                "type": "DIVERSIFICATION",
                "title": "Diversifisering anbefales",
                "description": "Vurder å diversifisere porteføljen din på tvers av flere sektorer for redusert risiko.",
                "stocks": []
            })
        
        return recommendations
    
    @staticmethod
    def send_weekly_email_report(user_email: str, report_data: Dict[str, Any]) -> bool:
        """Send weekly report via email"""
        from flask_mailman import EmailMessage
        from ..extensions import mail
        from flask import render_template_string
        
        try:
            # HTML email template
            email_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
                    .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .stock-item { border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; background: #f8f9fa; }
                    .positive { color: #28a745; }
                    .negative { color: #dc3545; }
                    .recommendation { background: #e7f3ff; border: 1px solid #007bff; padding: 15px; margin: 15px 0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 Ukentlig AI Aksje-Rapport</h1>
                        <p>{{ report_data.date }}</p>
                    </div>
                    
                    <div class="metric">
                        <h3>📊 Sammendrag</h3>
                        <p><strong>Totalt aksjer analysert:</strong> {{ report_data.total_stocks }}</p>
                        <p><strong>Topp-utøvere denne uken:</strong> {{ report_data.top_performers|length }}</p>
                    </div>
                    
                    <h3>🎯 AI Anbefalinger</h3>
                    {% for rec in report_data.recommendations %}
                    <div class="recommendation">
                        <h4>{{ rec.title }}</h4>
                        <p>{{ rec.description }}</p>
                    </div>
                    {% endfor %}
                    
                    <h3>📈 Watchlist Ytelse</h3>
                    {% for stock in report_data.ai_insights[:5] %}
                    <div class="stock-item">
                        <h4>{{ stock.symbol }}</h4>
                        <p>Pris: {{ "%.2f"|format(stock.current_price) }} NOK</p>
                        <p class="{% if stock.week_change > 0 %}positive{% else %}negative{% endif %}">
                            Uke-endring: {{ "%.2f"|format(stock.week_change) }}%
                        </p>
                        <p>AI Score: {{ "%.1f"|format(stock.ai_score) }}/10</p>
                    </div>
                    {% endfor %}
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p><small>Denne rapporten er generert av Aksjeradar AI. Ikke investeringsrådgivning.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_content = render_template_string(email_template, report_data=report_data)
            
            msg = EmailMessage(
                subject=f"🚀 Din ukentlige AI aksje-rapport - {report_data['date']}",
                recipients=[user_email],
                html=html_content
            )
            
            mail.send(msg)
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly email report: {e}")
            return False

class ConsultantReportService:
    """Service for generating on-demand consultant reports"""
    
    @staticmethod
    def generate_pdf_report(symbols: list, user_id: int) -> Optional[str]:
        """Generate comprehensive PDF report for specific stocks"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from io import BytesIO
            import os
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aksjeradar_rapport_{timestamp}.pdf"
            filepath = os.path.join("app", "static", "reports", filename)
            
            # Ensure reports directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # Center
            )
            story.append(Paragraph("🚀 Aksjeradar AI Konsulent-Rapport", title_style))
            story.append(Spacer(1, 12))
            
            # Date and summary
            story.append(Paragraph(f"Generert: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
            story.append(Paragraph(f"Analyserte aksjer: {', '.join(symbols)}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Analyze each stock
            for symbol in symbols:
                try:
                    analysis = get_ai_analysis(symbol)
                    
                    # Stock header
                    story.append(Paragraph(f"📊 {symbol}", styles['Heading2']))
                    story.append(Spacer(1, 12))
                    
                    # Key metrics table
                    data = [
                        ["Metrikk", "Verdi"],
                        ["Nåværende pris", f"{analysis.get('current_price', 0):,.2f} NOK"],
                        ["AI Score", f"{analysis.get('ai_score', 0):.1f}/10"],
                        ["Risiko nivå", analysis.get('risk_assessment', {}).get('level', 'Medium')],
                        ["Anbefalt handling", ConsultantReportService._get_recommendation(analysis.get('ai_score', 0))]
                    ]
                    
                    table = Table(data, colWidths=[2*inch, 2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 20))
                    
                    # AI Analysis
                    story.append(Paragraph("🤖 AI Analyse", styles['Heading3']))
                    
                    # Technical signals
                    signals = analysis.get('signals', [])
                    if signals:
                        story.append(Paragraph("Tekniske signaler:", styles['Normal']))
                        for signal in signals[:3]:  # Top 3 signals
                            story.append(Paragraph(f"• {signal.get('type', '')}: {signal.get('description', '')}", 
                                                 styles['Normal']))
                    
                    story.append(Spacer(1, 12))
                    
                    # Risk assessment
                    risk_data = analysis.get('risk_assessment', {})
                    story.append(Paragraph("Risikovurdering:", styles['Normal']))
                    story.append(Paragraph(f"• Volatilitet: {risk_data.get('volatility', 'Ukjent')}", styles['Normal']))
                    story.append(Paragraph(f"• Beta: {risk_data.get('beta', 'Ukjent')}", styles['Normal']))
                    
                    story.append(Spacer(1, 30))
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol} for PDF: {e}")
                    continue
            
            # Disclaimer
            story.append(Paragraph("⚠️ Ansvarsfraskrivelse", styles['Heading3']))
            disclaimer_text = """
            Denne rapporten er generert av Aksjeradar AI og er kun til informasjonsformål. 
            Den utgjør ikke investeringsrådgivning, og vi anbefaler å konsultere en kvalifisert 
            finansiell rådgiver før du tar investeringsbeslutninger. All investering innebærer risiko, 
            og tidligere resultater er ingen garanti for fremtidige resultater.
            """
            story.append(Paragraph(disclaimer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return None
    
    @staticmethod
    def _get_recommendation(ai_score: float) -> str:
        """Get recommendation based on AI score"""
        if ai_score >= 8:
            return "🟢 Sterk kjøp"
        elif ai_score >= 6:
            return "🟡 Kjøp"
        elif ai_score >= 4:
            return "⚪ Hold"
        elif ai_score >= 2:
            return "🟠 Selg"
        else:
            return "🔴 Sterk selg"
