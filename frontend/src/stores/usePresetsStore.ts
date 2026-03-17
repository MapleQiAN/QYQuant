import { defineStore } from 'pinia'
import {
  createStrategyPreset,
  deleteStrategyPreset,
  fetchStrategyPresets,
} from '../api/strategies'
import type { StrategyPreset } from '../types/Strategy'

export const usePresetsStore = defineStore('strategy-presets', {
  state: () => ({
    presets: [] as StrategyPreset[],
    loading: false,
    saving: false,
    deleting: false,
    error: null as string | null,
  }),
  actions: {
    async loadPresets(strategyId: string) {
      this.loading = true
      this.error = null
      try {
        this.presets = await fetchStrategyPresets(strategyId)
      } catch (error: any) {
        this.error = error?.message || 'Failed to load presets'
      } finally {
        this.loading = false
      }
    },
    async savePreset(strategyId: string, payload: { name: string; parameters: Record<string, unknown> }) {
      this.saving = true
      this.error = null
      try {
        const preset = await createStrategyPreset(strategyId, payload)
        this.presets = [preset, ...this.presets.filter((item) => item.id !== preset.id)]
        return preset
      } catch (error: any) {
        this.error = error?.message || 'Failed to save preset'
        throw error
      } finally {
        this.saving = false
      }
    },
    async removePreset(strategyId: string, presetId: string) {
      this.deleting = true
      this.error = null
      try {
        await deleteStrategyPreset(strategyId, presetId)
        this.presets = this.presets.filter((preset) => preset.id !== presetId)
      } catch (error: any) {
        this.error = error?.message || 'Failed to delete preset'
        throw error
      } finally {
        this.deleting = false
      }
    },
  },
})
