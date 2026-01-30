import { http, HttpResponse } from 'msw'
import { latestBacktest, recentBots, recentStrategies, hotPosts } from './data'

export const handlers = [
  http.get('/api/backtests/latest', () => HttpResponse.json(latestBacktest)),
  http.get('/api/bots/recent', () => HttpResponse.json(recentBots)),
  http.get('/api/strategies/recent', () => HttpResponse.json(recentStrategies)),
  http.get('/api/forum/hot', () => HttpResponse.json(hotPosts))
]
