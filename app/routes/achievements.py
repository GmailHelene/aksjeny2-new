"""
Achievements routes for gamification system
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..models.achievements import Achievement, UserAchievement, UserStats, check_user_achievements
from .. import db
from ..utils.access_control import demo_access, access_required
from datetime import datetime

achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')

@achievements_bp.route('/')
@access_required
def index():
    """Show user achievements page"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        # Show demo achievements page for non-authenticated users
        return render_template('achievements/index.html',
                             user_achievements=[],
                             available_achievements=[],
                             user_stats=None,
                             demo_mode=True)
    
    # Get user's earned achievements
    user_achievements = db.session.query(UserAchievement, Achievement).join(
        Achievement, UserAchievement.achievement_id == Achievement.id
    ).filter(UserAchievement.user_id == current_user.id).all()
    
    # Get available achievements not yet earned
    earned_ids = [ua.achievement_id for ua, a in user_achievements]
    available_achievements = Achievement.query.filter(
        ~Achievement.id.in_(earned_ids),
        Achievement.is_active == True
    ).all()
    
    # Get or create user stats
    user_stats = UserStats.query.filter_by(user_id=current_user.id).first()
    if not user_stats:
        user_stats = UserStats(user_id=current_user.id)
        db.session.add(user_stats)
        db.session.commit()
    
    return render_template('achievements/index.html',
                         user_achievements=user_achievements,
                         available_achievements=available_achievements,
                         user_stats=user_stats,
                         demo_mode=False)

@achievements_bp.route('/api/progress')
@access_required
def get_progress():
    """Get user's current progress for AJAX updates"""
    if not current_user.is_authenticated:
        return jsonify({
            'status': 'demo',
            'message': 'Please log in to track achievements'
        })
        
    user_stats = UserStats.query.filter_by(user_id=current_user.id).first()
    if not user_stats:
        user_stats = UserStats(user_id=current_user.id)
        db.session.add(user_stats)
        db.session.commit()
    
    return jsonify({
        'total_points': user_stats.total_points,
        'current_level': user_stats.current_level,
        'level_progress': user_stats.get_level_progress(),
        'consecutive_logins': user_stats.consecutive_login_days,
        'total_logins': user_stats.total_logins
    })

@achievements_bp.route('/api/update_stat', methods=['POST'])
@access_required
def update_stat():
    """Update user stat and check for new achievements"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'error': 'Please log in to track achievements',
            'demo_mode': True
        }), 401
    
    # Parse input data
    try:
        data = request.json
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': 'Invalid JSON data'
        }), 400
        
    stat_type = data.get('type')
    increment = data.get('increment', 1)
    
    if not stat_type:
        return jsonify({
            'success': False, 
            'error': 'Missing stat type'
        }), 400
    
    # Get or create user stats in a transaction
    try:
        user_stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if not user_stats:
            user_stats = UserStats(user_id=current_user.id)
            db.session.add(user_stats)
            db.session.flush()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error while accessing user stats'
        }), 500
    
    # Update the appropriate stat in a try block
    try:
        # Update the appropriate stat
        if stat_type == 'favorites':
            user_stats.favorites_added += increment
            new_value = user_stats.favorites_added
        elif stat_type == 'stocks_analyzed':
            user_stats.stocks_analyzed += increment
            new_value = user_stats.stocks_analyzed
        elif stat_type == 'portfolios':
            user_stats.portfolios_created += increment
            new_value = user_stats.portfolios_created
        elif stat_type == 'forum_posts':
            user_stats.forum_posts += increment
            new_value = user_stats.forum_posts
        elif stat_type == 'login':
            user_stats.update_consecutive_logins()
            new_value = user_stats.consecutive_login_days
            stat_type = 'consecutive_logins'  # For achievement checking
        else:
            return jsonify({
                'success': False, 
                'error': 'Unknown stat type'
            }), 400
        
        # Commit changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Database error while updating stats'
            }), 500
        
        # Check for new achievements
        try:
            new_achievements = check_user_achievements(current_user.id, stat_type, new_value)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Error checking achievements'
            }), 500
        
        # Return success with any new achievements
        return jsonify({
            'success': True,
            'new_achievements': [{
                'name': ach.name,
                'description': ach.description,
                'icon': ach.icon,
                'badge_color': ach.badge_color,
                'points': ach.points
            } for ach in new_achievements] if new_achievements else []
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error while updating stats'
        }), 500

@achievements_bp.route('/init')
def init_achievements():
    """Initialize default achievements - accessible to all for setup"""
    try:
        init_default_achievements()
        return jsonify({'success': True, 'message': 'Achievements initialized successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
