import React, { useState } from 'react'
import { InvoiceReport, InvoiceItem } from '@/types/invoice'
import { DownloadIcon } from './icons'

interface InvoiceTableProps {
  report: InvoiceReport
  onExportCSV: () => void
  onExportJSON: () => void
}

export default function InvoiceTable({ report, onExportCSV, onExportJSON }: InvoiceTableProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Get all items from all files
  const allItems: (InvoiceItem & { filename: string })[] = []
  Object.entries(report.files).forEach(([filename, fileData]) => {
    fileData.items.forEach(item => {
      allItems.push({ ...item, filename })
    })
  })

  // Filter items
  const filteredItems = allItems.filter(item => {
    const matchesPlatform = selectedPlatform === 'all' || item.platform === selectedPlatform
    const matchesSearch = searchTerm === '' || 
      item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.invoice_number.includes(searchTerm) ||
      (item.agency && item.agency.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.campaign_id && item.campaign_id.toLowerCase().includes(searchTerm.toLowerCase()))
    
    return matchesPlatform && matchesSearch
  })

  const platforms = ['all', ...Object.keys(report.summary.by_platform)]

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Invoice Details</h2>
        <div className="flex gap-2">
          <button
            onClick={onExportCSV}
            className="btn-secondary flex items-center gap-2"
          >
            <DownloadIcon className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={onExportJSON}
            className="btn-secondary flex items-center gap-2"
          >
            <DownloadIcon className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <select
          value={selectedPlatform}
          onChange={(e) => setSelectedPlatform(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {platforms.map(platform => (
            <option key={platform} value={platform}>
              {platform === 'all' ? 'All Platforms' : platform}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search invoices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Platform
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Invoice #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agency
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Campaign ID
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount (THB)
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredItems.map((item, index) => (
              <tr key={`${item.filename}-${item.line_number}-${index}`} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full
                    ${item.platform === 'Facebook' ? 'bg-blue-100 text-blue-800' : ''}
                    ${item.platform === 'Google' ? 'bg-green-100 text-green-800' : ''}
                    ${item.platform === 'TikTok' ? 'bg-purple-100 text-purple-800' : ''}
                  `}>
                    {item.platform}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={item.filename}>
                  {item.filename}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.invoice_number}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate" title={item.description}>
                  {item.description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.agency || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.campaign_id || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {item.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No invoices found matching your criteria
        </div>
      )}

      <div className="mt-4 text-sm text-gray-600">
        Showing {filteredItems.length} of {allItems.length} items
      </div>
    </div>
  )
}