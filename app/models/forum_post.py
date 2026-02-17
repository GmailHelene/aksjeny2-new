# This file is deprecated - ForumPost is now defined in app/models/forum.py
# Import from there instead to avoid SQLAlchemy mapping conflicts

from .forum import ForumPost

# Re-export for backwards compatibility
__all__ = ['ForumPost']
