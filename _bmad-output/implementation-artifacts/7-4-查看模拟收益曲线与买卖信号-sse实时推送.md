# Story 7.4: 查看模拟收益曲线与买卖信号（SSE 实时推送）

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为已登录用户，
我希望查看模拟收益曲线图和买卖信号记录，并在机器人执行后实时收到更新，
以便直观评估策略的模拟表现。

## Acceptance Criteria

1. **Given** 用户访问机器人详情页
   **When** 页面加载
   **Then** 调用 `GET /api/v1/simulation/bots/:id/records`，展示 `simulation_records` 数据生成的收益曲线图（FR45）
   **And** 若无数据，显示"暂无收益数据"占位

2. **Given** 用户访问机器人详情页
   **When** 页面加载
   **Then** 调用 `GET /api/v1/simulation/bots/:id/trades`，展示历史买卖信号记录列表（日期、标的、方向、价格）
   **And** 若无交易记录，显示"暂无买卖记录"占位

3. **Given** 机器人当日执行完毕（Celery Beat 任务写入新数据）
   **When** 用户保持详情页打开（SSE 连接：`GET /api/v1/simulation/bots/:bot_id/stream`）
   **Then** 服务端通过 SSE 推送最新持仓和收益数据，页面自动刷新图表（ARCH-12）

4. **Given** SSE 连接断开（网络波动或服务器断开）
   **When** 前端检测到连接关闭
   **Then** 前端自动重连，无需用户手动刷新

5. **Given** 用户尝试访问不属于自己的机器人数据
   **When** 调用任意 `/bots/:id/*` 端点
   **Then** 返回 `404` 和错误码 `BOT_NOT_FOUND`

6. **Given** 用户未登录
   **When** 访问任意 `/bots/:id/*` REST 端点
   **Then** 返回 `401 Unauthorized`

## Tasks / Subtasks

- [ ] Task 1: 后端 — 新增 `SimulationTrade` 模型与数据库迁移 (AC: #2)
  - [ ] 1.1 在 `backend/app/models.py` 末尾追加 `SimulationTrade` 模型：
    ```python
    class SimulationTrade(db.Model):
        __tablename__ = 'simulation_trades'
        __table_args__ = (
            db.Index('idx_simulation_trades_bot_id', 'bot_id'),
        )

        id = db.Column(db.String, primary_key=True, default=gen_id)
        bot_id = db.Column(db.String, db.ForeignKey('simulation_bots.id', ondelete='CASCADE'), nullable=False)
        trade_date = db.Column(db.Date, nullable=False)
        symbol = db.Column(db.String(20), nullable=False)
        side = db.Column(db.String(4), nullable=False)   # 'buy' | 'sell'
        price = db.Column(db.Numeric(18, 4), nullable=False)
        quantity = db.Column(db.Numeric(18, 4), nullable=False)
        created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, server_default=db.func.now())
    ```
  - [ ] 1.2 生成并执行 Alembic 迁移：
    ```bash
    cd backend && flask db migrate -m "add simulation_trades table"
    flask db upgrade
    ```

- [ ] Task 2: 后端 — 更新 `simulation_tasks.py` 以持久化买卖信号 (AC: #3)
  - [ ] 2.1 在 `_execute_single_bot` 中，修改调用 `execute_backtest_strategy` 之后的逻辑，提取并持久化 trades：
    ```python
    from ..models import SimulationBot, SimulationPosition, SimulationRecord, SimulationTrade

    # 在 db.session.commit() 之前插入：
    raw_trades = outcome.get('trades') or []
    for t in raw_trades:
        trade = SimulationTrade(
            bot_id=bot.id,
            trade_date=trade_date,
            symbol=t.get('symbol', ''),
            side=t.get('side', 'buy'),
            price=Decimal(str(t.get('price', 0))),
            quantity=Decimal(str(t.get('quantity', 0))),
        )
        db.session.add(trade)
    ```
  - [ ] 2.2 **⚠️ 关键**：`execute_backtest_strategy` 的返回值结构为 `{"trades": [...], "runtime": {...}}`（见 `backend/app/strategy_runtime/executor.py`）。但 `simulation_tasks.py` 还访问了 `outcome.get('equity')` 等字段——这些字段在当前 executor 返回值中 **不存在**，会静默回退到默认值。本 Story 不修复该设计问题，仅在现有逻辑末尾追加 trades 持久化即可。

- [ ] Task 3: 后端 — 在 `simulation.py` 蓝图中新增 REST 端点 (AC: #1, #2, #5, #6)
  - [ ] 3.1 新增 `GET /bots/:id/records` 端点（收益曲线数据）：
    ```python
    from ..models import SimulationBot, SimulationPosition, SimulationRecord, SimulationTrade

    @bp.get('/bots/<string:bot_id>/records')
    @jwt_required()
    def get_bot_records(bot_id: str):
        user_id = get_jwt_identity()
        bot = SimulationBot.query.filter_by(id=bot_id, user_id=user_id).first()
        if bot is None:
            return error_response('BOT_NOT_FOUND', '机器人不存在或无权访问', 404)

        records = (
            SimulationRecord.query
            .filter_by(bot_id=bot_id)
            .order_by(SimulationRecord.trade_date.asc())
            .all()
        )
        result = [
            {
                'trade_date': str(r.trade_date),
                'equity': f'{r.equity:.2f}',
                'cash': f'{r.cash:.2f}',
                'daily_return': f'{r.daily_return:.6f}',
            }
            for r in records
        ]
        return ok(result)
    ```
  - [ ] 3.2 新增 `GET /bots/:id/trades` 端点（买卖信号列表）：
    ```python
    @bp.get('/bots/<string:bot_id>/trades')
    @jwt_required()
    def get_bot_trades(bot_id: str):
        user_id = get_jwt_identity()
        bot = SimulationBot.query.filter_by(id=bot_id, user_id=user_id).first()
        if bot is None:
            return error_response('BOT_NOT_FOUND', '机器人不存在或无权访问', 404)

        trades = (
            SimulationTrade.query
            .filter_by(bot_id=bot_id)
            .order_by(SimulationTrade.trade_date.desc(), SimulationTrade.created_at.desc())
            .all()
        )
        result = [
            {
                'trade_date': str(t.trade_date),
                'symbol': t.symbol,
                'side': t.side,
                'price': f'{t.price:.4f}',
                'quantity': f'{t.quantity:.4f}',
            }
            for t in trades
        ]
        return ok(result)
    ```
  - [ ] 3.3 确认 `SimulationTrade` 已在文件顶部导入：
    ```python
    from ..models import SimulationBot, SimulationPosition, SimulationRecord, SimulationTrade, Strategy, User
    ```

- [ ] Task 4: 后端 — 新增 SSE 端点 `GET /bots/:id/stream` (AC: #3, #4, #5)
  - [ ] 4.1 在 `simulation.py` 中追加 SSE 端点：
    ```python
    import json
    import time
    from flask import Response, stream_with_context

    @bp.get('/bots/<string:bot_id>/stream')
    @jwt_required()
    def stream_bot(bot_id: str):
        """SSE 长连接：连接时立即推送当前状态，之后每 30 秒发送 heartbeat。
        当 Celery 任务写入新数据后，前端通过 EventSource 自动重连即可获取最新数据。
        """
        user_id = get_jwt_identity()
        bot = SimulationBot.query.filter_by(id=bot_id, user_id=user_id).first()
        if bot is None:
            return error_response('BOT_NOT_FOUND', '机器人不存在或无权访问', 404)

        def _snapshot():
            records = (
                SimulationRecord.query
                .filter_by(bot_id=bot_id)
                .order_by(SimulationRecord.trade_date.asc())
                .all()
            )
            positions = SimulationPosition.query.filter_by(bot_id=bot_id).all()
            return {
                'records': [
                    {
                        'trade_date': str(r.trade_date),
                        'equity': f'{r.equity:.2f}',
                        'daily_return': f'{r.daily_return:.6f}',
                    }
                    for r in records
                ],
                'positions': [
                    {
                        'symbol': p.symbol,
                        'quantity': f'{p.quantity:.4f}',
                        'avg_cost': f'{p.avg_cost:.4f}',
                    }
                    for p in positions
                ],
            }

        def generate():
            # 立即推送当前完整快照
            data = _snapshot()
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            # 每 30 秒发送 heartbeat 保持连接
            while True:
                time.sleep(30)
                yield ": heartbeat\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
            },
        )
    ```
  - [ ] 4.2 **⚠️ SSE 与 JWT**：`EventSource` 浏览器 API 不支持自定义 header，无法传递 `Authorization: Bearer <token>`。
    解决方案：在 SSE 端点改为接受 URL query 参数 `?token=<jwt>` 并手动验证：
    ```python
    from flask import request
    from flask_jwt_extended import decode_token
    from jwt.exceptions import InvalidTokenError

    @bp.get('/bots/<string:bot_id>/stream')
    def stream_bot(bot_id: str):
        token = request.args.get('token', '')
        try:
            decoded = decode_token(token)
            user_id = decoded['sub']
        except Exception:
            return error_response('UNAUTHORIZED', '无效 token', 401)
        # ... 其余逻辑不变
    ```
    前端 `EventSource` 传 token：
    ```typescript
    const es = new EventSource(`/api/v1/simulation/bots/${botId}/stream?token=${accessToken}`)
    ```
    **安全提示**：token 暴露在 URL 中会被记录在服务器日志，生产中考虑改用 cookie 鉴权或 POST 握手换取临时 stream token。

- [ ] Task 5: 后端 — 测试 (AC: #1–#6)
  - [ ] 5.1 在 `backend/tests/test_simulation.py` 中追加以下测试用例：
    - `test_get_records_empty`：无 records 时返回 200 + 空 data 数组
    - `test_get_records_returns_data`：有 records 时返回 trade_date、equity、cash、daily_return
    - `test_get_records_bot_not_found`：bot_id 不存在返回 404 + BOT_NOT_FOUND
    - `test_get_records_other_user_bot`：访问他人机器人返回 404
    - `test_get_records_unauthenticated`：无 JWT 返回 401
    - `test_get_trades_empty`：无 trades 时返回 200 + 空 data 数组
    - `test_get_trades_returns_data`：有 trades 时返回 trade_date、symbol、side、price、quantity
    - `test_get_trades_bot_not_found`：404 + BOT_NOT_FOUND
    - `test_get_trades_unauthenticated`：无 JWT 返回 401
  - [ ] 5.2 SSE 端点不需单元测试（需要长连接，集成测试复杂度过高），在测试文件中添加简短注释说明此决定。
  - [ ] 5.3 新增 fixtures：
    ```python
    @pytest.fixture
    def sim_record(db_session, sim_bot):
        """为已有 sim_bot 创建一条模拟收益记录"""
        from app.models import SimulationRecord
        from decimal import Decimal
        from datetime import date
        rec = SimulationRecord(
            bot_id=sim_bot.id,
            trade_date=date(2026, 3, 20),
            equity=Decimal('105000.00'),
            cash=Decimal('55000.00'),
            daily_return=Decimal('0.000500'),
        )
        db_session.add(rec)
        db_session.commit()
        return rec

    @pytest.fixture
    def sim_trade(db_session, sim_bot):
        """为已有 sim_bot 创建一条买卖信号记录"""
        from app.models import SimulationTrade
        from decimal import Decimal
        from datetime import date
        trade = SimulationTrade(
            bot_id=sim_bot.id,
            trade_date=date(2026, 3, 20),
            symbol='000001.XSHG',
            side='buy',
            price=Decimal('15.2300'),
            quantity=Decimal('1000.0000'),
        )
        db_session.add(trade)
        db_session.commit()
        return trade
    ```

- [ ] Task 6: 前端 — 扩展 `Simulation.ts` 类型定义 (AC: #1, #2)
  - [ ] 6.1 在 `frontend/src/types/Simulation.ts` 末尾追加：
    ```typescript
    export interface SimulationRecord {
      trade_date: string       // 'YYYY-MM-DD'
      equity: string           // Numeric → string
      cash: string             // Numeric → string
      daily_return: string     // Numeric → string
    }

    export interface SimulationTrade {
      trade_date: string       // 'YYYY-MM-DD'
      symbol: string
      side: 'buy' | 'sell'
      price: string            // Numeric → string
      quantity: string         // Numeric → string
    }

    export interface SimBotStreamPayload {
      records: Pick<SimulationRecord, 'trade_date' | 'equity' | 'daily_return'>[]
      positions: Pick<SimulationPosition, 'symbol' | 'quantity' | 'avg_cost'>[]
    }
    ```

- [ ] Task 7: 前端 — 扩展 `api/simulation.ts`，新增 API 函数 (AC: #1, #2)
  - [ ] 7.1 在 `frontend/src/api/simulation.ts` 末尾追加：
    ```typescript
    import type {
      CreateBotPayload, SimulationBot, SimulationPosition,
      SimulationRecord, SimulationTrade
    } from '../types/Simulation'

    export function getSimRecords(botId: string): Promise<SimulationRecord[]> {
      return client.request({
        method: 'get',
        url: `/v1/simulation/bots/${botId}/records`,
      })
    }

    export function getSimTrades(botId: string): Promise<SimulationTrade[]> {
      return client.request({
        method: 'get',
        url: `/v1/simulation/bots/${botId}/trades`,
      })
    }
    ```
  - [ ] 7.2 SSE 工具函数（**不通过 axios**，使用原生 `EventSource`）追加到 `api/simulation.ts`：
    ```typescript
    import type { SimBotStreamPayload } from '../types/Simulation'

    /**
     * 创建 SSE 连接，连接时立即触发 onMessage 回调（含初始快照）。
     * 返回 EventSource 实例，调用方负责在 onUnmounted 中调用 .close()。
     */
    export function createBotStream(
      botId: string,
      accessToken: string,
      onMessage: (payload: SimBotStreamPayload) => void,
      onError?: (e: Event) => void,
    ): EventSource {
      const url = `/api/v1/simulation/bots/${botId}/stream?token=${encodeURIComponent(accessToken)}`
      const es = new EventSource(url)
      es.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as SimBotStreamPayload
          onMessage(payload)
        } catch {
          // malformed event, ignore
        }
      }
      if (onError) es.onerror = onError
      return es
    }
    ```
    **注意**：`EventSource` 有内置自动重连机制，断线后浏览器会自动重试，无需手动重连逻辑。

- [ ] Task 8: 前端 — 新建 `BotDetailModal.vue` 组件 (AC: #1, #2, #3, #4)
  - [ ] 8.1 创建 `frontend/src/components/simulation/BotDetailModal.vue`：
    ```vue
    <template>
      <div class="modal-overlay" @click.self="emit('close')">
        <div class="modal-content modal-content--wide">
          <div class="modal-header">
            <h2>{{ bot.strategy_name }} — 详情</h2>
            <span class="modal-status-badge" :class="`status-${bot.status}`">{{ statusLabel }}</span>
            <button class="btn-icon" @click="emit('close')">✕</button>
          </div>

          <!-- 收益曲线 -->
          <section class="detail-section">
            <h3 class="section-title">收益曲线</h3>
            <div v-if="isLoading" class="loading-spinner">加载中...</div>
            <div v-else-if="records.length === 0" class="empty-hint">暂无收益数据（机器人尚未运行）</div>
            <SimulationChart v-else :records="records" />
          </section>

          <!-- 买卖信号 -->
          <section class="detail-section">
            <h3 class="section-title">买卖信号记录</h3>
            <div v-if="isLoading" class="loading-spinner">加载中...</div>
            <div v-else-if="trades.length === 0" class="empty-hint">暂无买卖记录</div>
            <table v-else class="trades-table">
              <thead>
                <tr>
                  <th>日期</th><th>标的</th><th>方向</th><th>价格</th><th>数量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(t, i) in trades" :key="i" :class="`side-${t.side}`">
                  <td>{{ t.trade_date }}</td>
                  <td>{{ t.symbol }}</td>
                  <td class="side-label">{{ t.side === 'buy' ? '买入' : '卖出' }}</td>
                  <td>¥ {{ t.price }}</td>
                  <td>{{ t.quantity }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </div>
    </template>

    <script setup lang="ts">
    import { computed, onMounted, onUnmounted, ref } from 'vue'
    import { useAuthStore } from '@/stores/user'
    import { getSimRecords, getSimTrades, createBotStream } from '@/api/simulation'
    import type { SimulationBot, SimulationRecord, SimulationTrade } from '@/types/Simulation'
    import SimulationChart from './SimulationChart.vue'

    const props = defineProps<{ bot: SimulationBot }>()
    const emit = defineEmits<{ (e: 'close'): void }>()

    const authStore = useAuthStore()
    const records = ref<SimulationRecord[]>([])
    const trades = ref<SimulationTrade[]>([])
    const isLoading = ref(false)
    let eventSource: EventSource | null = null

    const statusLabel = computed(() => ({
      active: '运行中',
      paused: '已暂停',
      stopped: '已停止',
    }[props.bot.status] ?? props.bot.status))

    onMounted(async () => {
      isLoading.value = true
      try {
        const [recs, trds] = await Promise.all([
          getSimRecords(props.bot.id),
          getSimTrades(props.bot.id),
        ])
        records.value = recs
        trades.value = trds
      } finally {
        isLoading.value = false
      }

      // 建立 SSE 连接以实时更新收益曲线
      const token = authStore.accessToken  // 确认 store 中 access token 的实际字段名
      if (token) {
        eventSource = createBotStream(
          props.bot.id,
          token,
          (payload) => {
            // SSE 返回的 records 是精简版，仅更新图表数据
            records.value = payload.records as SimulationRecord[]
          },
        )
      }
    })

    onUnmounted(() => {
      eventSource?.close()
    })
    </script>
    ```
  - [ ] 8.2 **⚠️ 关键陷阱 — authStore access token 字段名**：
    `BotDetailModal.vue` 需要从 `useAuthStore()` 中获取当前 JWT access token 以传给 SSE 端点。
    **开发前必须**读 `frontend/src/stores/user.ts`（或 `useAuthStore.ts`），确认 access token 的实际字段名（可能是 `accessToken`、`token`、`state.token` 等）。
    **不要假设字段名**——错误的字段名会导致 token 为 undefined，SSE 连接 401 失败。

- [ ] Task 9: 前端 — 新建 `SimulationChart.vue` 组件 (AC: #1)
  - [ ] 9.1 创建 `frontend/src/components/simulation/SimulationChart.vue`：
    ```vue
    <template>
      <div ref="chartRef" class="sim-chart-canvas"></div>
    </template>

    <script setup lang="ts">
    import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
    import * as echarts from 'echarts'
    import type { ECharts, EChartsOption } from 'echarts'
    import type { SimulationRecord } from '@/types/Simulation'

    const props = defineProps<{ records: SimulationRecord[] }>()

    const chartRef = ref<HTMLDivElement | null>(null)
    let chart: ECharts | null = null
    let resizeObserver: ResizeObserver | null = null

    function buildOption(): EChartsOption {
      if (!props.records.length) {
        return {
          title: {
            text: '暂无收益曲线数据',
            left: 'center',
            top: 'middle',
            textStyle: { color: '#64748b', fontSize: 14 },
          },
        }
      }
      return {
        animation: false,
        tooltip: {
          trigger: 'axis',
          valueFormatter: (v) =>
            Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }),
        },
        xAxis: {
          type: 'category',
          data: props.records.map((r) => r.trade_date),
          axisLabel: { rotate: 30, fontSize: 10 },
        },
        yAxis: { type: 'value', name: '净值 (¥)' },
        series: [
          {
            name: '模拟权益',
            type: 'line',
            data: props.records.map((r) => Number(r.equity)),
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 2 },
            areaStyle: { opacity: 0.1 },
          },
        ],
      }
    }

    onMounted(() => {
      if (!chartRef.value) return
      chart = echarts.init(chartRef.value)
      chart.setOption(buildOption())
      resizeObserver = new ResizeObserver(() => chart?.resize())
      resizeObserver.observe(chartRef.value)
    })

    watch(() => props.records, () => chart?.setOption(buildOption()), { deep: true })

    onBeforeUnmount(() => {
      resizeObserver?.disconnect()
      chart?.dispose()
    })
    </script>

    <style scoped>
    .sim-chart-canvas {
      width: 100%;
      height: 300px;
    }
    </style>
    ```
  - [ ] 9.2 参考模式：`frontend/src/components/backtest/EquityCurveChart.vue` — 使用相同的 echarts + ResizeObserver 模式，保持代码风格一致。

- [ ] Task 10: 前端 — 更新 `BotCard.vue`，新增"查看详情"按钮 (AC: #1, #2, #3)
  - [ ] 10.1 在 `frontend/src/components/simulation/BotCard.vue` 的 `bot-card__actions` 区域追加"查看详情"按钮：
    ```vue
    <button class="btn-primary btn-sm" @click="emit('view-detail', bot.id)">
      查看详情
    </button>
    ```
  - [ ] 10.2 在 `defineEmits` 中添加 `'view-detail'` 事件：
    ```typescript
    const emit = defineEmits<{
      (e: 'view-positions', id: string): void
      (e: 'view-detail', id: string): void
    }>()
    ```

- [ ] Task 11: 前端 — 更新 `BotsView.vue`，挂载 `BotDetailModal` (AC: #1, #2, #3)
  - [ ] 11.1 在 `frontend/src/views/BotsView.vue` 中追加：
    - 新增 `selectedDetailBot` ref（`SimulationBot | null`）
    - 在 `BotCard` 上监听 `@view-detail="openDetail"` 事件
    - 在模板末尾追加 `<BotDetailModal>` 弹窗：
    ```vue
    <BotDetailModal
      v-if="selectedDetailBot"
      :bot="selectedDetailBot"
      @close="selectedDetailBot = null"
    />
    ```
    - 在 `<script setup>` 中追加：
    ```typescript
    import BotDetailModal from '@/components/simulation/BotDetailModal.vue'
    import type { SimulationBot } from '@/types/Simulation'

    const selectedDetailBot = ref<SimulationBot | null>(null)

    function openDetail(botId: string) {
      selectedDetailBot.value = simulationStore.bots.find(b => b.id === botId) ?? null
    }
    ```

- [ ] Task 12: 前端 — 测试 (AC: #1–#4)
  - [ ] 12.1 在 `frontend/src/api/simulation.test.ts` 中追加：
    - `getSimRecords` 调用 `GET /v1/simulation/bots/:id/records`
    - `getSimTrades` 调用 `GET /v1/simulation/bots/:id/trades`
  - [ ] 12.2 新建 `frontend/src/components/simulation/SimulationChart.test.ts`：
    - 传入空 records 时渲染"暂无收益曲线数据"提示
    - 传入有效 records 时，echarts mock 被调用（mock echarts.init）
  - [ ] 12.3 新建 `frontend/src/components/simulation/BotDetailModal.test.ts`：
    - 挂载后调用 `getSimRecords` 和 `getSimTrades`（并行 Promise.all）
    - 有 records 时渲染 `SimulationChart`
    - 无 trades 时显示"暂无买卖记录"
    - 点击背景层触发 `'close'` emit
    - `onUnmounted` 时调用 `eventSource.close()`

## Dev Notes

### 架构约束与关键模式

- **蓝图文件**：`backend/app/blueprints/simulation.py`（Stories 7.1–7.3 已有，本 Story 在同一文件追加端点）
- **认证**：REST 端点使用 `@jwt_required()`；SSE 端点因 `EventSource` 不支持自定义 header，改用 URL query token (`?token=<jwt>`) + 手动 `decode_token`
- **响应格式**：REST 端点用 `ok(data)` / `error_response(code, message, status)` 封装；SSE 端点直接返回 `Response` 对象
- **SSE MIME 类型**：必须设置 `content_type='text/event-stream'`，浏览器才会识别为 SSE
- **SSE 自动重连**：浏览器原生 `EventSource` 在连接断开后自动重连，无需前端额外实现；heartbeat 注释行（`: heartbeat\n\n`）用于保持连接，不触发 `onmessage`
- **前端状态**：SSE 数据直接更新组件局部 state（`records`），不通过 Pinia store（避免多个 BotDetailModal 实例产生 store 冲突）
- **图表库**：使用 ECharts（`"echarts": "^6.0.0"`），参考 `frontend/src/components/backtest/EquityCurveChart.vue` 的实现模式
- **数字类型**：后端所有 `Numeric` 字段序列化为字符串（如 `f'{value:.2f}'`），前端接收后用 `Number(str)` 转换才能用于图表

### ⚠️ 关键陷阱 1：`SimulationTrade` 模型为新增，需迁移

`simulation_trades` 表在当前 DB schema 中 **不存在**（Stories 7.1–7.3 未创建）。必须先执行 Alembic 迁移，否则任何写入/查询都会抛出 `ProgrammingError: relation "simulation_trades" does not exist`。

```bash
cd backend && flask db migrate -m "add simulation_trades table" && flask db upgrade
```

### ⚠️ 关键陷阱 2：authStore access token 字段名

`BotDetailModal.vue` 需要 JWT token 传给 SSE URL。**开发前必须**读 `frontend/src/stores/user.ts`，确认 access token 的实际 state 字段名，以及该 token 是否随 API 响应自动刷新后同步到 store。

### ⚠️ 关键陷阱 3：SSE 端点不能使用 `@jwt_required()` 装饰器

Flask-JWT-Extended 的 `@jwt_required()` 从 `Authorization` header 读取 token，而浏览器 `EventSource` **无法设置自定义 header**。必须改为从 URL query string 中提取 token 并手动调用 `decode_token()`。

### ⚠️ 关键陷阱 4：`execute_backtest_strategy` 返回结构与 simulation_tasks 的不匹配

`executor.py:execute_backtest_strategy` 返回 `{"trades": [...], "runtime": {...}}`，不包含 `equity`、`cash`、`positions`。但 `simulation_tasks.py` 目前对这些字段回退到默认值（静默失败）。这是 Story 7.2 遗留问题，本 Story **不修复**，仅追加 `trades` 持久化逻辑。

### Project Structure Notes

新增/修改文件列表：
- `backend/app/models.py` — 追加 `SimulationTrade` 模型
- `backend/migrations/versions/<hash>_add_simulation_trades_table.py` — 新 Alembic 迁移
- `backend/app/blueprints/simulation.py` — 追加 3 个端点（records、trades、stream）
- `backend/app/tasks/simulation_tasks.py` — 追加 trades 持久化
- `backend/tests/test_simulation.py` — 追加测试用例和 fixtures
- `frontend/src/types/Simulation.ts` — 追加 3 个类型
- `frontend/src/api/simulation.ts` — 追加 3 个函数（getSimRecords、getSimTrades、createBotStream）
- `frontend/src/components/simulation/SimulationChart.vue` — 新建
- `frontend/src/components/simulation/BotDetailModal.vue` — 新建
- `frontend/src/components/simulation/BotCard.vue` — 追加 view-detail 按钮
- `frontend/src/views/BotsView.vue` — 追加 BotDetailModal 挂载
- `frontend/src/api/simulation.test.ts` — 追加测试
- `frontend/src/components/simulation/SimulationChart.test.ts` — 新建
- `frontend/src/components/simulation/BotDetailModal.test.ts` — 新建

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md` — 领域6: 模拟托管 — SSE 架构设计 (ARCH-12)]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 7.4 验收标准]
- [Source: `backend/app/blueprints/simulation.py` — 现有端点模式（认证、响应格式）]
- [Source: `backend/app/strategy_runtime/executor.py` — execute_backtest_strategy 返回结构]
- [Source: `backend/app/tasks/simulation_tasks.py` — 现有 Celery 任务实现]
- [Source: `backend/app/models.py` — SimulationRecord/SimulationPosition/BacktestTrade 模型定义]
- [Source: `frontend/src/components/backtest/EquityCurveChart.vue` — ECharts + ResizeObserver 模式]
- [Source: `_bmad-output/implementation-artifacts/7-3-查看机器人运行状态与持仓.md` — 前序 Story 组件结构与测试模式]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
