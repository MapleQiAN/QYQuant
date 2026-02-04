from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Backtest, BotInstance, File, Post, Strategy, StrategyVersion, User
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
    db.session.flush()

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

    gold_strategy = Strategy(
        name='黄金策略 Step-By-Step',
        symbol='XAUUSD',
        status='running',
        returns=0,
        win_rate=0,
        max_drawdown=0,
        tags=['gold', 'breakout', 'step-by-step'],
        last_update=now_ms(),
        trades=0,
        owner_id=admin.id,
    )
    db.session.add(gold_strategy)
    db.session.flush()

    gold_file = File(
        owner_id=admin.id,
        filename='GoldStepByStep.qys',
        content_type='application/zip',
        size=8972,
        path='backend/strategy_store/GoldStepByStep.qys',
    )
    db.session.add(gold_file)
    db.session.flush()

    gold_version = StrategyVersion(
        strategy_id=gold_strategy.id,
        version='0.1.0',
        file_id=gold_file.id,
        checksum='4f969e331ef2f7e3c90997ee3e1f9d9035f286c99653938d9de8a53de9aa76bc',
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

    db.session.add_all([strat, post, bot, bt, gold_version])
    db.session.commit()
    print('seed ok')
