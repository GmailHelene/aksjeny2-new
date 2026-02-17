"""Blog routes"""
from flask import Blueprint, render_template, redirect, url_for

blog = Blueprint('blog', __name__)

@blog.route('/')
@blog.route('/index')
def index():
    """Blog index page - redirect to main for now"""
    # TODO: Implement blog functionality
    return redirect(url_for('main.index'))
