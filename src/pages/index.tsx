import React, { useState } from 'react'
import Head from 'next/head'
import FileUpload from '@/components/FileUpload'
import InvoiceTable from '@/components/InvoiceTable'
import SummaryCard from '@/components/SummaryCard'
import { SpinnerIcon } from '@/components/icons'
import { InvoiceReport, ProcessingResult } from '@/types/invoice'
import axios from 'axios'
import toast from 'react-hot-toast'

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [report, setReport] = useState<InvoiceReport | null>(null)
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  // Check backend status on mount
  React.useEffect(() => {
    const checkBackend = async () => {
      try {
        await axios.get('https://peepong.pythonanywhere.com/api/health')
        setBackendStatus('online')
      } catch (error) {
        setBackendStatus('offline')
      }
    }
    checkBackend()
  }, [])

  const handleFilesSelected = async (files: File[]) => {
    if (files.length === 0) return

    setIsProcessing(true)
    const formData = new FormData()
    
    files.forEach((file) => {
      formData.append('files', file)
    })

    try {
      // First check if backend is running
      try {
        await axios.get('https://peepong.pythonanywhere.com/api/health')
      } catch (healthError) {
        toast.error('Backend server is not running. Please check the connection.')
        setIsProcessing(false)
        return
      }

      const response = await axios.post<ProcessingResult>(
        'https://peepong.pythonanywhere.com/api/process-invoices',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout
        }
      )

      if (response.data.success && response.data.data) {
        setReport(response.data.data)
        toast.success(`Successfully processed ${files.length} file(s)`)
      } else {
        toast.error(response.data.message || 'Failed to process invoices')
      }
    } catch (error) {
      console.error('Error processing invoices:', error)
      if (axios.isAxiosError(error)) {
        if (error.response?.data?.message) {
          toast.error(error.response.data.message)
        } else if (error.code === 'ECONNABORTED') {
          toast.error('Request timeout. Please try with fewer files.')
        } else {
          toast.error('Failed to process invoices. Please try again.')
        }
      } else {
        toast.error('An unexpected error occurred')
      }
    } finally {
      setIsProcessing(false)
    }
  }

  const handleExportCSV = async () => {
    if (!report) return

    try {
      const response = await axios.post(
        'https://peepong.pythonanywhere.com/api/export-csv',
        report,
        {
          responseType: 'blob',
        }
      )

      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `invoice_report_${new Date().toISOString().split('T')[0]}.csv`
      link.click()
      
      toast.success('CSV exported successfully')
    } catch (error) {
      console.error('Error exporting CSV:', error)
      toast.error('Failed to export CSV')
    }
  }

  const handleExportJSON = () => {
    if (!report) return

    const dataStr = JSON.stringify(report, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `invoice_report_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    
    toast.success('JSON exported successfully')
  }

  return (
    <>
      <Head>
        <title>Invoice Reader App</title>
        <meta name="description" content="Parse and analyze invoices from Facebook, Google, and TikTok" />
      </Head>

      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 mb-2">Invoice Reader App</h1>
                <p className="text-lg text-gray-600">
                  Upload and analyze invoices from Facebook, Google, and TikTok
                </p>
              </div>
              <div className="text-sm">
                Backend Status: 
                <span className={`ml-2 font-semibold ${
                  backendStatus === 'online' ? 'text-green-600' : 
                  backendStatus === 'offline' ? 'text-red-600' : 
                  'text-yellow-600'
                }`}>
                  {backendStatus === 'online' ? '● Online' : 
                   backendStatus === 'offline' ? '● Offline' : 
                   '● Checking...'}
                </span>
              </div>
            </div>
          </div>

          {backendStatus === 'offline' && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">
                ⚠️ Backend server is offline. Please start the Flask server:
              </p>
              <pre className="mt-2 text-sm bg-red-100 p-2 rounded">
                cd backend{'\n'}
                python app.py
              </pre>
            </div>
          )}

          <div className="mb-8">
            <FileUpload 
              onFilesSelected={handleFilesSelected}
              isProcessing={isProcessing}
            />
          </div>

          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-16">
              <SpinnerIcon className="w-12 h-12 text-primary-600 mb-4" />
              <p className="text-lg text-gray-600">Processing invoices...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
            </div>
          )}

          {report && !isProcessing && (
            <>
              <SummaryCard report={report} />
              <InvoiceTable 
                report={report}
                onExportCSV={handleExportCSV}
                onExportJSON={handleExportJSON}
              />
            </>
          )}
        </div>
      </main>
    </>
  )
}