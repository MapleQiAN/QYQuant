from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Backtest, BotInstance, Post, Strategy, User
from app.utils.time import now_ms

app = create_app('development')

with app.app_context():
    db.create_all()
    admin = User(
        email='admin@example.com',
        name='Admin',
        avatar='',
        password_hash=generate_password_hash('admin123'),
    )
    db.session.add(admin)

    strat = Strategy(
        name='SMA Cross',
        symbol='BTCUSDT',
        status='running',
        returns=0.12,
        win_rate=0.55,
        max_drawdown=0.08,
        tags=['sma'],
        last_update=now_ms(),
        trades=12,
    )
    post = Post(
        title='My first strategy',
        author='Admin',
        avatar='',
        likes=12,
        comments=3,
        timestamp=now_ms(),
        tags=['share'],
    )
    bot = BotInstance(
        name='BTC Bot',
        strategy='SMA Cross',
        status='active',
        profit=120.5,
        runtime='7d',
        capital=10000,
        tags=['paper'],
        paper=True,
    )
    bt = Backtest(
        name='BTC Backtest',
        symbol='BTCUSDT',
        status='completed',
        started_at=now_ms(),
        finished_at=now_ms(),
    )

    db.session.add_all([strat, post, bot, bt])
    db.session.commit()
    print('seed ok')
