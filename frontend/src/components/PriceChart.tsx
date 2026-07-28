import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { PricePoint } from '../types'

export default function PriceChart({ title, series, unit }: { title: string; series: PricePoint[]; unit: string }) {
  const data = series.map((p) => ({ date: p.price_date.slice(5), price: p.price }))

  return (
    <div className="panel" style={{ padding: '18px 18px 8px', flex: 1, minWidth: 280 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>{title}</div>
      {data.length === 0 ? (
        <div style={{ color: 'var(--text-dim)', fontSize: 13, padding: '30px 0', textAlign: 'center' }}>
          No price history yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={data} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--border-soft)" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--text-dim)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: 'var(--text-dim)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--panel-raised)',
                border: '1px solid var(--border)',
                borderRadius: 3,
                fontSize: 12,
              }}
              labelStyle={{ color: 'var(--text-muted)' }}
              formatter={(value: number) => [`${value.toFixed(2)} ${unit}`, 'price']}
            />
            <Line type="monotone" dataKey="price" stroke="var(--brass)" strokeWidth={1.75} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
