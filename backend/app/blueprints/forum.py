from flask import request
from flask_smorest import Blueprint

from ..extensions import db
from ..models import Comment, Favorite, Like, Post, Tip
from ..schemas import PostSchema
from ..utils.response import ok
from ..utils.time import now_ms

bp = Blueprint('forum', __name__, url_prefix='/api/forum')


@bp.get('/hot')
def hot():
    posts = Post.query.order_by(Post.likes.desc()).limit(10).all()
    return ok(PostSchema(many=True).dump(posts))


@bp.post('/posts')
def create_post():
    payload = request.get_json() or {}
    post = Post(
        title=payload.get('title', ''),
        author=payload.get('author', ''),
        avatar=payload.get('avatar', ''),
        likes=0,
        comments=0,
        timestamp=now_ms(),
        tags=payload.get('tags', []),
    )
    db.session.add(post)
    db.session.commit()
    return ok(PostSchema().dump(post))
