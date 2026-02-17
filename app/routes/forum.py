from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models.forum import ForumPost, ForumTopic
from app.models.user import User
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, ValidationError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

forum = Blueprint('forum', __name__)

@forum.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    """Soft-delete a forum topic (author or admin)."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError as e:
        logger.warning(f"CSRF validation failed (delete_topic): {e}")
        return jsonify({'success': False, 'error': 'csrf_failed'}), 400

    topic = ForumTopic.query.filter_by(id=topic_id).first()
    if not topic:
        return jsonify({'success': False, 'error': 'not_found'}), 404

    if current_user.id != topic.author_id and not getattr(current_user, 'is_admin', False):
        return jsonify({'success': False, 'error': 'unauthorized'}), 403

    try:
        topic.is_active = False
        for p in topic.posts:
            p.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'topic_deleted', 'topic_id': topic_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error soft-deleting topic {topic_id}: {e}")
        return jsonify({'success': False, 'error': 'delete_failed'}), 500

@forum.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Soft-delete a forum post (author or admin)."""
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError as e:
        logger.warning(f"CSRF validation failed (delete_post): {e}")
        return jsonify({'success': False, 'error': 'csrf_failed'}), 400

    post = ForumPost.query.filter_by(id=post_id).first()
    if not post:
        return jsonify({'success': False, 'error': 'not_found'}), 404

    if current_user.id != post.author_id and not getattr(current_user, 'is_admin', False):
        return jsonify({'success': False, 'error': 'unauthorized'}), 403

    try:
        post.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'post_deleted', 'post_id': post_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error soft-deleting post {post_id}: {e}")
        return jsonify({'success': False, 'error': 'delete_failed'}), 500

@forum.route('/')
def index():
    """Forum main page with real statistics"""
    try:
        # Get real forum statistics
        total_posts = ForumPost.query.count()
        total_topics = ForumPost.query.count()  # Each post is a topic for now
        total_members = User.query.count()
        
        # Get recent posts for the main listing
        posts = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(20).all()
        
        # Get recent topics for sidebar
        recent_topics = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(5).all()
        
        # Calculate online users (simplified: users active in last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        online_now = 1  # At least the current user is online
        
    except Exception as e:
        logger.error(f"Forum index error: {e}")
        # Fallback data when forum_posts table doesn't exist
        total_posts = 0
        total_topics = 0
        total_members = 1  # At least 1 user (the current one)
        posts = []
        recent_topics = []
        online_now = 1
    
    # Create categories with actual data (avoid showing 0s)
    categories = [
        {
            'name': 'Aksjeanalyse',
            'description': 'Diskuter spesifikke aksjer og deres utvikling',
            'icon': 'bi bi-graph-up',
            'topics': total_topics,
            'posts': total_posts
        },
        {
            'name': 'Markedstrender',
            'description': 'Generelle markedstrender og økonomiske nyheter',
            'icon': 'bi bi-trending-up',
            'topics': 0,  # Separate category stats
            'posts': 0
        },
        {
            'name': 'Investeringsstrategier',
            'description': 'Del og diskuter ulike investeringsstrategier',
            'icon': 'bi bi-lightbulb',
            'topics': 0,  # Separate category stats
            'posts': 0
        }
    ]
    
    return render_template('forum/index.html', 
                         posts=posts, 
                         categories=categories,
                         recent_topics=recent_topics,
                         total_members=total_members,
                         online_now=online_now)

@forum.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError as e:
            logger.warning(f"CSRF validation failed: {e}")
            flash('Sikkerhetsfeil: Vennligst prøv igjen.', 'error')
            return redirect(url_for('forum.create'))
            
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Tittel og innhold er påkrevd.', 'error')
            return redirect(url_for('forum.create'))
        post = ForumPost(
            title=title, 
            content=content, 
            user_id=current_user.id,
            author_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Innlegg opprettet!', 'success')
        return redirect(url_for('forum.index'))
    return render_template('forum/create.html')

# Alias for create_topic (used in template)
@forum.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    """Create a new forum topic with robust error handling"""
    try:
        if request.method == 'POST':
            # Validate CSRF token
            try:
                validate_csrf(request.form.get('csrf_token'))
            except ValidationError as e:
                logger.warning(f"CSRF validation failed: {e}")
                flash('Sikkerhetsfeil: Vennligst prøv igjen.', 'error')
                return render_template('forum/create_topic.html')
            
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            category = request.form.get('category', 'general')
            
            if not title or not content:
                flash('Tittel og innhold er påkrevd.', 'error')
                return render_template('forum/create_topic.html')
                
            # Create the forum post with proper error handling
            try:
                # Ensure we have all required database tables
                db.create_all()
                
                # Create the post
                post = ForumPost(
                    title=title,
                    content=content,
                    user_id=current_user.id,
                    author_id=current_user.id
                )
                
                # Try to add category if the field exists
                if hasattr(ForumPost, 'category'):
                    post.category = category
                
                db.session.add(post)
                db.session.commit()
                
                flash('Innlegg opprettet!', 'success')
                logger.info(f"Forum post created successfully by user {current_user.id}: {title}")
                return redirect(url_for('forum.index'))
                
            except Exception as db_error:
                logger.error(f"Database error creating forum post: {db_error}")
                db.session.rollback()
                flash('Kunne ikke opprette innlegg. Prøv igjen senere.', 'error')
                return render_template('forum/create_topic.html')
                
        # GET request - show form
        categories = [
            {'id': 'aksjeanalyse', 'name': 'Aksjeanalyse'},
            {'id': 'markedstrender', 'name': 'Markedstrender'},
            {'id': 'investeringsstrategier', 'name': 'Investeringsstrategier'},
            {'id': 'general', 'name': 'Generelt'}
        ]
        
        return render_template('forum/create_topic.html', categories=categories)
        
    except Exception as e:
        logger.error(f"Critical error in create_topic: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        flash('En teknisk feil oppsto. Prøv igjen senere.', 'error')
        return redirect(url_for('forum.index'))

@forum.route('/category/<category_name>')
def category(category_name):
    """Category view with proper error handling"""
    try:
        # Handle invalid category names
        if category_name == '---' or not category_name.strip():
            flash('Ugyldig kategori.', 'error')
            return redirect(url_for('forum.index'))
        
        # Get posts - in the future this could be filtered by actual category
        posts = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(20).all()
        
        return render_template('forum/category.html', 
                             posts=posts, 
                             category_name=category_name.replace('-', ' ').title())
    except Exception as e:
        logger.error(f"Forum category error for {category_name}: {e}")
        flash('Kunne ikke laste kategori.', 'error')
        return redirect(url_for('forum.index'))

@forum.route('/topic/<topic_id>')
def topic(topic_id):
    """Topic view with proper error handling"""
    try:
        # Handle invalid topic IDs
        if topic_id == '---' or not str(topic_id).isdigit():
            flash('Ugyldig emne-ID.', 'error')
            return redirect(url_for('forum.index'))
        
        # Alias for view route
        return view(int(topic_id))
    except ValueError:
        flash('Ugyldig emne-ID.', 'error')
        return redirect(url_for('forum.index'))
    except Exception as e:
        logger.error(f"Forum topic error for {topic_id}: {e}")
        flash('Kunne ikke laste emne.', 'error')
        return redirect(url_for('forum.index'))

@forum.route('/search')
def search():
    """Enhanced search supporting multi-term OR matching with lightweight relevance scoring.

    Behaviour:
    - Split sanitized query on whitespace into tokens (max 6 tokens to cap complexity)
    - Build OR filter across (title ILIKE %token% OR content ILIKE %token%) for any token
    - Compute relevance_score in Python (title hit = 1 per token, content hit = 0.5) capped at 5.0
    - Sort posts by relevance_score desc then created_at desc
    - Gracefully handle empty / invalid queries.
    """
    try:
        raw_query = request.args.get('q', '')
        query = (raw_query or '').strip()
        MAX_LEN = 50
        if len(query) > MAX_LEN:
            query = query[:MAX_LEN]
        import re
        allowed_pattern = re.compile(r'^[A-Za-z0-9ÆØÅæøå_\- ]+$')
        if query and not allowed_pattern.match(query):
            query = ''.join(ch for ch in query if ch.isalnum() or ch in (' ', '-', '_'))
            query = query.strip()
        if not query:
            class _Results:
                def __init__(self, items):
                    self.items = items
                    self.total = len(items)
            return render_template('forum/search.html', posts=[], query='', forum_categories={}, results=_Results([]))
        # Tokenize
        tokens = [t for t in re.split(r'\s+', query) if t]
        tokens = tokens[:6]
        lowered_tokens = [t.lower() for t in tokens]
        # Build dynamic OR filter
        conditions = []
        if len(tokens) == 1:
            tok = tokens[0]
            conditions.append(db.or_(ForumPost.title.ilike(f"%{tok}%"), ForumPost.content.ilike(f"%{tok}%")))
        else:
            for tok in tokens:
                conditions.append(db.or_(ForumPost.title.ilike(f"%{tok}%"), ForumPost.content.ilike(f"%{tok}%")))
        q = ForumPost.query.filter(db.or_(*conditions)).order_by(ForumPost.created_at.desc()).limit(200).all()
        # Score, enrich, and sort
        enriched = []
        for p in q:
            try:
                title_l = (p.title or '').lower()
                content_l = (p.content or '').lower()
                score = 0.0
                for tok in lowered_tokens:
                    if tok in title_l:
                        score += 1.0
                    elif tok in content_l:
                        score += 0.5
                relevance_score = round(score, 3)
                # Build snippet (first 180 chars of content)
                snippet = (p.content or '')[:180]
                # Build author/avatar
                author = getattr(p, 'author', None)
                author_name = author.username if author and hasattr(author, 'username') else getattr(p, 'author_name', 'Ukjent')
                author_avatar = getattr(author, 'avatar_url', None) if author and hasattr(author, 'avatar_url') else None
                # Category display
                category_display = getattr(p, 'category', None)
                if category_display:
                    category_display = str(category_display).title()
                else:
                    category_display = 'Generelt'
                # Type (topic/post)
                result_type = 'topic' if hasattr(p, 'is_topic') and p.is_topic else 'post'
                # Reply count
                reply_count = getattr(p, 'reply_count', 0)
                # Match type (title/content)
                match_type = 'Tittel' if any(tok in title_l for tok in lowered_tokens) else ('Innhold' if any(tok in content_l for tok in lowered_tokens) else '')
                # URL for post detail
                url = url_for('forum.topic', topic_id=p.id)
                enriched.append({
                    'id': p.id,
                    'title': p.title,
                    'snippet': snippet,
                    'author': author_name,
                    'author_avatar': author_avatar,
                    'category_display': category_display,
                    'type': result_type,
                    'reply_count': reply_count,
                    'match_type': match_type,
                    'relevance_score': relevance_score,
                    'created_at': p.created_at,
                    'url': url
                })
            except Exception as e:
                enriched.append({
                    'id': getattr(p, 'id', None),
                    'title': getattr(p, 'title', ''),
                    'snippet': '',
                    'author': 'Ukjent',
                    'author_avatar': None,
                    'category_display': 'Generelt',
                    'type': 'post',
                    'reply_count': 0,
                    'match_type': '',
                    'relevance_score': 0.0,
                    'created_at': getattr(p, 'created_at', None),
                    'url': url_for('forum.topic', topic_id=getattr(p, 'id', 0))
                })
        enriched.sort(key=lambda p: (p['relevance_score'], p['created_at']), reverse=True)
        class _Results:
            def __init__(self, items):
                self.items = items
                self.total = len(items)
                self.pages = 1
                self.page = 1
                self.has_prev = False
                self.has_next = False
            def iter_pages(self):
                return [1]
        results = _Results(enriched[:50])  # cap final display
        return render_template('forum/search.html', posts=enriched[:50], query=query, forum_categories={}, results=results)
    except Exception as e:
        logger.error(f"Forum search error for query '{locals().get('query','')}' : {e}")
        class _Results:
            def __init__(self, items):
                self.items = items
                self.total = len(items)
        return render_template('forum/search.html', posts=[], query=locals().get('query',''), forum_categories={}, results=_Results([]), error="Søket kunne ikke utføres. Prøv igjen.")

@forum.route('/api/search')
def api_search():
    """JSON forum search with multi-term OR matching, scoring, caching & rate limiting.

    Query semantics:
    - Split on whitespace into tokens (max 8)
    - Match any token in title/content (case-insensitive, substring)
    - Score: title hit = 1, content hit = 0.5 per token; included in result.
    - Backwards compatible fields retained.
    """
    from app.utils.api_response import ok, fail
    try:
        import time, re
        from sqlalchemy import or_
        raw_query = request.args.get('q', '') or ''
        query = raw_query.strip()
        MAX_LEN = 50
        if len(query) > MAX_LEN:
            query = query[:MAX_LEN]
        allowed_pattern = re.compile(r'^[A-Za-z0-9ÆØÅæøå_\- ]+$')
        if query and not allowed_pattern.match(query):
            query = ''.join(ch for ch in query if ch.isalnum() or ch in (' ', '-', '_', '-'))
            query = query.strip()
        auth_flag = getattr(current_user, 'is_authenticated', False)
        if not query:
            return ok({'query': '', 'results': [], 'data_points': 0}, cache_hit=False, data_source='EMPTY_QUERY', authenticated=auth_flag)

        # Rate limiting
        global _FORUM_SEARCH_RATE
        try:
            _FORUM_SEARCH_RATE
        except NameError:
            _FORUM_SEARCH_RATE = {}
        ip = request.remote_addr or 'unknown'
        now = time.time()
        window = 30
        bucket = _FORUM_SEARCH_RATE.get(ip, [])
        bucket = [t for t in bucket if now - t < window]
        if len(bucket) >= 30:
            return fail('rate_limited', data={'query': query, 'results': [], 'data_points': 0, 'retry_after': window}, cache_hit=False, data_source='RATE_LIMIT', authenticated=auth_flag)
        bucket.append(now)
        _FORUM_SEARCH_RATE[ip] = bucket

        # Caching (token-based key)
        global _FORUM_SEARCH_CACHE
        try:
            _FORUM_SEARCH_CACHE
        except NameError:
            _FORUM_SEARCH_CACHE = {}
        tokens = [t for t in re.split(r'\s+', query) if t]
        tokens = tokens[:8]
        lowered_tokens = [t.lower() for t in tokens]
        CACHE_TTL = 20
        cache_key = '::'.join(['qapi'] + lowered_tokens)
        entry = _FORUM_SEARCH_CACHE.get(cache_key)
        if entry and (now - entry['ts']) < CACHE_TTL:
            cached = entry['results']
            return ok({'query': query, 'results': cached, 'data_points': len(cached)}, cache_hit=True, data_source='CACHE', authenticated=auth_flag)

        # Build SQL OR conditions (use sqlalchemy.or_ for reliability – some db instances may not expose db.or_)
        conditions = []
        for tok in tokens:
            like = f"%{tok}%"
            conditions.append(or_(ForumPost.title.ilike(like), ForumPost.content.ilike(like)))
        if not conditions:
            # Should not happen because empty query handled above, but guard anyway
            return ok({'query': query, 'results': [], 'data_points': 0}, cache_hit=False, data_source='EMPTY_TOKENS', authenticated=auth_flag)
        query_set = ForumPost.query.filter(or_(*conditions)).order_by(ForumPost.created_at.desc()).limit(300).all()

        results = []
        for p in query_set:
            title_l = (p.title or '').lower()
            content_l = (p.content or '').lower()
            score = 0.0
            matched_tokens = []
            for tok in lowered_tokens:
                if tok in title_l:
                    score += 1.0
                    matched_tokens.append(tok)
                elif tok in content_l:
                    score += 0.5
                    matched_tokens.append(tok)
            if score == 0.0:
                continue  # Should not happen due to filter, but guard
            results.append({
                'id': p.id,
                'title': p.title,
                'excerpt': (p.content[:120] + '...') if p.content and len(p.content) > 123 else p.content,
                'created_at': p.created_at.isoformat() if getattr(p, 'created_at', None) else None,
                'author_id': p.author_id,
                'score': round(score, 3),
                'matched_tokens': matched_tokens
            })
        # Sort & truncate
        results.sort(key=lambda r: (r['score'], r.get('created_at') or ''), reverse=True)
        results = results[:100]
        _FORUM_SEARCH_CACHE[cache_key] = {'results': results, 'ts': now}
        return ok({'query': query, 'results': results, 'data_points': len(results)}, cache_hit=False, data_source='DB', authenticated=auth_flag)
    except Exception as e:
        # Provide richer diagnostics in the response to aid test debugging (still success False)
        logger.error(f"Forum API search error for query '{locals().get('query','')}' : {e}", exc_info=True)
        return fail('internal_error', data={'query': locals().get('query',''), 'results': [], 'data_points': 0}, cache_hit=False, data_source='ERROR', authenticated=getattr(current_user, 'is_authenticated', False))

@forum.route('/<int:post_id>')
def view(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('forum/view.html', post=post)

@forum.route('/api/posts')
def api_posts():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

@forum.route('/api/post/<int:post_id>')
def api_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return jsonify(post.to_dict())
