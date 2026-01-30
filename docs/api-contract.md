# QYQuant API Contract

Base URL: /api

## Success Envelope
{ "code": 0, "message": "ok", "data": { ... }, "request_id": "..." }

## Errors
HTTP status + { "code": <status>00, "message": "...", "details": null }

## Endpoints
- GET /backtests/latest -> BacktestLatestResponse
- POST /backtests/run -> { job_id }
- GET /backtests/job/{job_id} -> { status, result? }
- GET /bots/recent -> Bot[]
- POST /bots -> Bot
- PATCH /bots/{id}/status -> Bot
- GET /bots/{id}/performance -> { equity: [], orders: [] }
- GET /strategies/recent -> Strategy[]
- GET /forum/hot -> Post[]
- POST /auth/login -> { access_token }
- GET /users/me -> User
