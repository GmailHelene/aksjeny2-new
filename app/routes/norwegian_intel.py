from flask import Blueprint, render_template, current_app
from flask_login import login_required

norwegian_intel = Blueprint('norwegian_intel', __name__)

@norwegian_intel.route('/')
@login_required
def index():
    return render_template('norwegian_intel/index.html', title='Norge Oversikt', placeholder=True)

@norwegian_intel.route('/social-sentiment')
@login_required
def social_sentiment():
    return render_template('norwegian_intel/placeholder.html', title='Sosial sentiment', feature='Sosial sentiment')

@norwegian_intel.route('/oil-correlation')
@login_required
def oil_correlation():
    return render_template('norwegian_intel/placeholder.html', title='Olje-korrelasjon', feature='Olje-korrelasjon')

@norwegian_intel.route('/government-impact')
@login_required
def government_impact():
    return render_template('norwegian_intel/placeholder.html', title='Regjeringsanalyse', feature='Regjeringsanalyse')

@norwegian_intel.route('/shipping-intelligence')
@login_required
def shipping_intelligence():
    return render_template('norwegian_intel/placeholder.html', title='Shipping Intelligence', feature='Shipping Intelligence')
