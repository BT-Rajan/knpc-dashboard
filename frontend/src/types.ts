export interface NavItem {
  code: string
  name: string
}

export interface NavCategory {
  category: string
  items: NavItem[]
}

export interface TickerEntry {
  code: string
  name: string
  category: string
  unit: string
  current_price: number | null
  previous_price: number | null
  daily_change: number | null
  daily_change_pct: number | null
  as_of: string | null
}

export interface PricePoint {
  price_date: string
  price: number
}

export interface NewsOut {
  headline: string
  url: string | null
  source: string | null
  collected_at: string
}

export interface ItemDetail {
  code: string
  name: string
  category: string
  unit: string
  current_price: number | null
  previous_price: number | null
  daily_change: number | null
  daily_change_pct: number | null
  as_of: string | null
  weekly_series: PricePoint[]
  monthly_series: PricePoint[]
  news: NewsOut[]
}

export interface SourceOut {
  id: number
  item_id: number
  name: string
  url: string
  source_type: string
  value_selector: string
  news_selector: string | null
  priority: number
  active: boolean
}

export interface ItemOut {
  id: number
  code: string
  name: string
  category: string
  unit: string
  active: boolean
  sources: SourceOut[]
}

export interface ScrapeLogOut {
  run_at: string
  item_code: string | null
  source_name: string | null
  status: string
  message: string | null
}

export interface ScrapeSettingOut {
  frequency_minutes: number
}

export interface AIAskResponse {
  provider: string
  answer: string
}
