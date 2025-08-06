'use client';

import { useState, useCallback } from 'react';

// Define the structure of the unified data model for TypeScript
interface IUnifiedInvoice {
  source_filename: string | null;
  platform: string | null;
  invoice_type: string | null;
  invoice_id: string | null;
  invoice_date: string | null;
  due_date: string | null;
  client_name: string | null;
  billing_period: string | null;
  total_amount: number | null;
  currency: string | null;
  line_item_description: string | null;
  line_item_amount: number | null;
  line_item_period: string | null;
  line_item_project_id: string | null;
  line_item_project_name: string | null;
  line_item_campaign_id: string | null;
  line_item_objective: string | null;
  line_item_agency: string | null;
}

export default function InvoicesPage() {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedData, setProcessedData] = useState<IUnifiedInvoice[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(event.target.files);
    setProcessedData([]); // Reset data when new files are selected
    setError(null); // Reset error state
  };

  const handleProcessInvoices = useCallback(async () => {
    if (!selectedFiles) return;

    setIsProcessing(true);
    setError(null);
    console.log(`Uploading ${selectedFiles.length} files for processing...`);

    const formData = new FormData();
    Array.from(selectedFiles).forEach(file => {
      formData.append('files', file);
    });

    try {
      // The backend is running on port 5001
      const response = await fetch('http://localhost:5001/api/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Processing failed on the server.');
      }

      const data: IUnifiedInvoice[] = await response.json();
      setProcessedData(data);
      console.log('Processing complete.', data);

    } catch (err: any) {
      console.error('Error processing invoices:', err);
      setError(err.message || 'An unknown error occurred.');
    } finally {
      setIsProcessing(false);
    }
  }, [selectedFiles]);

  const convertToCSV = (data: IUnifiedInvoice[]) => {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [
        headers.join(',') // Header row
    ];

    data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header as keyof IUnifiedInvoice];
            const strValue = value === null || value === undefined ? '' : String(value);
            // Handle commas and quotes in values
            return `"${strValue.replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
    });

    return csvRows.join('\n');
  };

  const handleExportCSV = () => {
    if (processedData.length === 0) return;

    const csvData = convertToCSV(processedData);
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'processed_invoices.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Invoice Auto-Processor</h1>

      <div className="p-4 border rounded-lg bg-gray-50">
        <h2 className="text-xl font-semibold mb-2">1. Upload Invoices</h2>
        <p className="text-sm text-gray-600 mb-4">
          Select one or more PDF invoice files. The system will automatically detect the platform and type.
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,image/*"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-violet-50 file:text-violet-700 hover:file:bg-violet-100"
        />
        {selectedFiles && <p className="mt-2 text-sm text-gray-500">{selectedFiles.length} file(s) selected.</p>}
      </div>

      <div className="mt-4">
        <button
          onClick={handleProcessInvoices}
          disabled={!selectedFiles || isProcessing}
          className="w-full px-4 py-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Processing...' : '2. Process Invoices'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 border border-red-400 rounded-lg">
            <p className="font-bold">An Error Occurred:</p>
            <p>{error}</p>
        </div>
      )}

      {processedData.length > 0 && (
        <div className="mt-8">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold">3. Processed Data</h2>
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
            >
              Export to CSV
            </button>
          </div>
          <div className="border rounded-lg overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(processedData[0]).map(key => (
                    <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{key.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processedData.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value: any, i) => (
                      <td key={i} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{value === null ? '' : String(value)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}