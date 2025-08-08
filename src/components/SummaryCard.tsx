import React from 'react'
import { InvoiceReport } from '@/types/invoice'

interface SummaryCardProps {
  report: InvoiceReport
}

export default function SummaryCard({ report }: SummaryCardProps) {
  const { summary } = report

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Files</h3>
        <p className="text-3xl font-bold text-primary-600">
          {summary.overall.files_processed}
        </p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Items</h3>
        <p className="text-3xl font-bold text-primary-600">
          {summary.overall.total_items.toLocaleString()}
        </p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Amount</h3>
        <p className="text-3xl font-bold text-primary-600">
          ฿{summary.overall.total_amount.toLocaleString('en-US', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
          })}
        </p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Platforms</h3>
        <div className="space-y-2">
          {Object.entries(summary.by_platform).map(([platform, data]) => (
            <div key={platform} className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-600">{platform}:</span>
              <span className="text-sm font-bold text-gray-900">
                ฿{data.total_amount.toLocaleString('en-US', { 
                  minimumFractionDigits: 0, 
                  maximumFractionDigits: 0 
                })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}