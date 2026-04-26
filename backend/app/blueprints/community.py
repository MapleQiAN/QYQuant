from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from ..extensions import db
from ..models import Post, PostComment, PostInteraction, Strategy, User
from ..utils.response import error_response, ok
from ..utils.time import format_beijing_iso, now_ms, now_utc
from ..tasks.moderation_tasks import moderate_content

bp = Blueprint("community", __name__, url_prefix="/api/v1")


def _int_arg(name, *, default, minimum=None, maximum=None):
    raw = request.args.get(name)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _get_community_post_or_404(post_id):
    post = db.session.get(Post, post_id)
    if post is None or post.content is None:
        return None, error_response("POST_NOT_FOUND", "post not found", 404)
    return post, None


def _author_payload(post, author):
    return {
        "nickname": getattr(author, "nickname", None) or post.author or "",
        "avatar_url": getattr(author, "avatar_url", None) or post.avatar or "",
    }


def _strategy_payload(strategy):
    if strategy is None:
        return None
    return {
        "id": strategy.id,
        "name": strategy.name,
        "category": strategy.category,
        "returns": strategy.returns,
        "max_drawdown": strategy.max_drawdown,
    }


def _interaction_state_map(user_id, post_ids):
    if not user_id or not post_ids:
        return {}, {}

    rows = (
        PostInteraction.query
        .filter(
            PostInteraction.user_id == user_id,
            PostInteraction.post_id.in_(post_ids),
            PostInteraction.type.in_(["like", "collect"]),
        )
        .all()
    )
    liked = {}
    collected = {}
    for row in rows:
        if row.type == "like":
            liked[row.post_id] = True
        elif row.type == "collect":
            collected[row.post_id] = True
    return liked, collected


def _serialize_post(post, *, author=None, strategy=None, liked=False, collected=False):
    return {
        "id": post.id,
        "content": post.content or "",
        "user_id": post.user_id,
        "strategy_id": post.strategy_id,
        "likes_count": post.likes_count or 0,
        "comments_count": post.comments_count or 0,
        "created_at": format_beijing_iso(post.created_at),
        "author": _author_payload(post, author),
        "strategy": _strategy_payload(strategy),
        "liked": liked,
        "collected": collected,
    }


def _serialize_comment(comment, *, author=None):
    return {
        "id": comment.id,
        "content": comment.content,
        "user_id": comment.user_id,
        "created_at": format_beijing_iso(comment.created_at),
        "author": {
            "nickname": getattr(author, "nickname", None) or "",
            "avatar_url": getattr(author, "avatar_url", None) or "",
        },
    }


@bp.post("/posts")
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return error_response("UNAUTHORIZED", "user not found", 401)
    if user.is_banned:
        return error_response("FORBIDDEN", "account is banned", 403)

    payload = request.get_json() or {}
    content = str(payload.get("content") or "").strip()
    raw_strategy_id = payload.get("strategy_id")
    strategy_id = str(raw_strategy_id).strip() if raw_strategy_id else None

    if not content:
        return error_response("CONTENT_REQUIRED", "content is required", 422)
    if len(content) > 2000:
        return error_response("CONTENT_TOO_LONG", "content must be 2000 characters or fewer", 422)

    strategy = None
    if strategy_id is not None:
        strategy = db.session.get(Strategy, strategy_id)
        if strategy is None:
            return error_response("STRATEGY_NOT_FOUND", "strategy not found", 404)

    created_at = now_utc()
    post = Post(
        title=content[:80] or "Community Post",
        author=user.nickname or "",
        avatar=user.avatar_url or "",
        likes=0,
        comments=0,
        timestamp=now_ms(),
        tags=[],
        user_id=user.id,
        content=content,
        strategy_id=strategy_id,
        likes_count=0,
        comments_count=0,
        created_at=created_at,
    )
    db.session.add(post)
    db.session.commit()

    moderate_content.delay(
        user_id=user.id,
        target_type="post",
        target_id=post.id,
        content=content,
    )

    return ok(_serialize_post(post, author=user, strategy=strategy, liked=False, collected=False))


@bp.get("/posts")
@jwt_required(optional=True)
def get_posts():
    user_id = get_jwt_identity()
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=50)

    base_query = Post.query.filter(Post.content.isnot(None), Post.is_hidden.is_(False))
    total = base_query.count()
    posts = (
        base_query
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    author_ids = {post.user_id for post in posts if post.user_id}
    authors = {user.id: user for user in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    strategy_ids = {post.strategy_id for post in posts if post.strategy_id}
    strategies = {strategy.id: strategy for strategy in Strategy.query.filter(Strategy.id.in_(strategy_ids)).all()} if strategy_ids else {}
    liked_map, collected_map = _interaction_state_map(user_id, [post.id for post in posts])

    items = [
        _serialize_post(
            post,
            author=authors.get(post.user_id),
            strategy=strategies.get(post.strategy_id),
            liked=liked_map.get(post.id, False),
            collected=collected_map.get(post.id, False),
        )
        for post in posts
    ]
    return ok({"items": items, "total": total, "page": page, "per_page": per_page})


@bp.get("/posts/<post_id>")
@jwt_required(optional=True)
def get_post_detail(post_id):
    user_id = get_jwt_identity()
    post, error = _get_community_post_or_404(post_id)
    if error:
        return error

    author = db.session.get(User, post.user_id) if post.user_id else None
    strategy = db.session.get(Strategy, post.strategy_id) if post.strategy_id else None
    liked_map, collected_map = _interaction_state_map(user_id, [post.id])
    return ok(
        _serialize_post(
            post,
            author=author,
            strategy=strategy,
            liked=liked_map.get(post.id, False),
            collected=collected_map.get(post.id, False),
        )
    )


def _check_active_user(user_id):
    """Return (user, error_response) — rejects deleted or banned users."""
    user = db.session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        return None, error_response("UNAUTHORIZED", "user not found", 401)
    if user.is_banned:
        return None, error_response("FORBIDDEN", "account is banned", 403)
    return user, None


@bp.post("/posts/<post_id>/like")
@jwt_required()
def toggle_like(post_id):
    user_id = get_jwt_identity()
    _user, user_error = _check_active_user(user_id)
    if user_error:
        return user_error
    post, error = _get_community_post_or_404(post_id)
    if error:
        return error

    existing = (
        PostInteraction.query
        .filter_by(user_id=user_id, post_id=post.id, type="like")
        .first()
    )
    if existing is None:
        db.session.add(PostInteraction(user_id=user_id, post_id=post.id, type="like"))
        Post.query.filter_by(id=post.id).update({Post.likes_count: Post.likes_count + 1})
        liked = True
    else:
        db.session.delete(existing)
        Post.query.filter_by(id=post.id).update(
            {Post.likes_count: db.case((Post.likes_count > 0, Post.likes_count - 1), else_=0)}
        )
        liked = False

    db.session.commit()
    refreshed = db.session.get(Post, post.id)
    return ok({"liked": liked, "likes_count": refreshed.likes_count or 0})


@bp.post("/posts/<post_id>/collect")
@jwt_required()
def toggle_collect(post_id):
    user_id = get_jwt_identity()
    _user, user_error = _check_active_user(user_id)
    if user_error:
        return user_error
    post, error = _get_community_post_or_404(post_id)
    if error:
        return error

    existing = (
        PostInteraction.query
        .filter_by(user_id=user_id, post_id=post.id, type="collect")
        .first()
    )
    if existing is None:
        db.session.add(PostInteraction(user_id=user_id, post_id=post.id, type="collect"))
        collected = True
    else:
        db.session.delete(existing)
        collected = False

    db.session.commit()
    return ok({"collected": collected})


@bp.get("/users/me/collections")
@jwt_required()
def get_my_collections():
    user_id = get_jwt_identity()
    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=50)

    base_query = (
        db.session.query(Post)
        .join(PostInteraction, PostInteraction.post_id == Post.id)
        .filter(
            PostInteraction.user_id == user_id,
            PostInteraction.type == "collect",
            Post.content.isnot(None),
            Post.is_hidden.is_(False),
        )
    )
    total = base_query.count()
    posts = (
        base_query
        .order_by(PostInteraction.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    author_ids = {p.user_id for p in posts if p.user_id}
    authors = {u.id: u for u in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    strategy_ids = {p.strategy_id for p in posts if p.strategy_id}
    strategies = {s.id: s for s in Strategy.query.filter(Strategy.id.in_(strategy_ids)).all()} if strategy_ids else {}
    liked_map, collected_map = _interaction_state_map(user_id, [p.id for p in posts])

    items = [
        _serialize_post(
            p,
            author=authors.get(p.user_id),
            strategy=strategies.get(p.strategy_id),
            liked=liked_map.get(p.id, False),
            collected=collected_map.get(p.id, False),
        )
        for p in posts
    ]
    return ok({"items": items, "total": total, "page": page, "per_page": per_page})


@bp.get("/posts/<post_id>/comments")
def get_comments(post_id):
    post, error = _get_community_post_or_404(post_id)
    if error:
        return error

    page = _int_arg("page", default=1, minimum=1)
    per_page = _int_arg("per_page", default=20, minimum=1, maximum=50)
    query = PostComment.query.filter_by(post_id=post.id, is_hidden=False)
    total = query.count()
    comments = (
        query
        .order_by(PostComment.created_at.asc(), PostComment.id.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    author_ids = {comment.user_id for comment in comments if comment.user_id}
    authors = {user.id: user for user in User.query.filter(User.id.in_(author_ids)).all()} if author_ids else {}
    items = [_serialize_comment(comment, author=authors.get(comment.user_id)) for comment in comments]
    return ok({"items": items, "total": total, "page": page, "per_page": per_page})


@bp.post("/posts/<post_id>/comments")
@jwt_required()
def create_comment(post_id):
    user_id = get_jwt_identity()
    _user, user_error = _check_active_user(user_id)
    if user_error:
        return user_error
    post, error = _get_community_post_or_404(post_id)
    if error:
        return error

    payload = request.get_json() or {}
    content = str(payload.get("content") or "").strip()
    if not content:
        return error_response("CONTENT_REQUIRED", "content is required", 422)
    if len(content) > 500:
        return error_response("CONTENT_TOO_LONG", "content must be 500 characters or fewer", 422)

    comment = PostComment(
        post_id=post.id,
        user_id=user_id,
        content=content,
        created_at=now_utc(),
    )
    db.session.add(comment)
    Post.query.filter_by(id=post.id).update({Post.comments_count: Post.comments_count + 1})
    db.session.commit()

    moderate_content.delay(
        user_id=user_id,
        target_type="comment",
        target_id=comment.id,
        content=content,
    )

    author = db.session.get(User, user_id)
    return ok(_serialize_comment(comment, author=author))
