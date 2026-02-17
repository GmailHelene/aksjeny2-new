from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from models import db, ForumTopic, Portfolio, Stock

forum_portfolio_bp = Blueprint('forum_portfolio', __name__)

class TopicForm(FlaskForm):
    title = StringField('Tittel', validators=[DataRequired()])
    content = TextAreaField('Innhold', validators=[DataRequired()])

@forum_portfolio_bp.route('/forum/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    form = TopicForm()
    if form.validate_on_submit():
        try:
            topic = ForumTopic(
                title=form.title.data,
                content=form.content.data,
                user_id=current_user.id
            )
            db.session.add(topic)
            db.session.commit()
            flash('Emnet ble opprettet!', 'success')
            return redirect(url_for('forum.view_topic', id=topic.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Kunne ikke opprette emne: {str(e)}', 'error')
    
    return render_template('forum/create_topic.html', form=form)

@forum_portfolio_bp.route('/portfolio/create', methods=['GET', 'POST'])
@login_required
def create_portfolio():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        try:
            portfolio = Portfolio(
                name=name,
                description=description,
                user_id=current_user.id
            )
            db.session.add(portfolio)
            db.session.commit()
            flash(f'Porteføljen "{name}" ble opprettet!', 'success')
            return redirect(url_for('portfolio.view', id=portfolio.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Kunne ikke opprette portefølje: {str(e)}', 'error')
    
    return render_template('portfolio/create.html')

@forum_portfolio_bp.route('/portfolio/<int:id>/add', methods=['POST'])
@login_required
def add_to_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    
    if portfolio.user_id != current_user.id:
        flash('Du har ikke tilgang til denne porteføljen', 'error')
        return redirect(url_for('portfolio.list'))
    
    ticker = request.form.get('ticker')
    shares = request.form.get('shares', type=float)
    purchase_price = request.form.get('purchase_price', type=float)
    
    try:
        stock = Stock(
            ticker=ticker,
            shares=shares,
            purchase_price=purchase_price,
            portfolio_id=portfolio.id
        )
        db.session.add(stock)
        db.session.commit()
        flash(f'{ticker} ble lagt til porteføljen!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Kunne ikke legge til aksje: {str(e)}', 'error')
    
    return redirect(url_for('portfolio.view', id=id))
