import React, { useState, useEffect } from 'react';

interface ExtractedData {
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  vendor_name?: string;
  client_name?: string;
  currency?: string;
  total_amount?: number;
  billing_period?: string;
  invoice_type?: string;
  line_items?: any[];
  description?: string; // For non-AP invoices
}

interface InvoiceData {
  id: number;
  filename: string;
  status: string;
  error_message?: string;
  extracted_data?: ExtractedData;
  created_at: string;
  updated_at: string;
}

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState('');
  const [processedInvoices, setProcessedInvoices] = useState<InvoiceData[]>([]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFiles(event.target.files);
    }
  };

  const handleUpload = async () => {
    if (!files) {
      setMessage('Please select files to upload.');
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      setMessage('Uploading and queuing files for processing...');
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        // Optionally, refresh the list of invoices immediately to show pending ones
        fetchProcessedInvoices();
      } else {
        setMessage(`Error: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage(`Network error: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const fetchProcessedInvoices = async () => {
    try {
      const response = await fetch('http://localhost:5000/invoices');
      if (response.ok) {
        const data = await response.json();
        setProcessedInvoices(data.invoices);
      } else {
        console.error('Failed to fetch processed invoices');
      }
    } catch (error) {
      console.error('Network error fetching invoices:', error);
    }
  };

  // Polling to update processed invoices list
  useEffect(() => {
    fetchProcessedInvoices(); // Fetch initially
    const interval = setInterval(() => {
      fetchProcessedInvoices();
    }, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Invoice Reader</h1>
      <input type="file" multiple onChange={handleFileChange} accept=".pdf" />
      <button onClick={handleUpload} style={{ marginLeft: '10px' }}>Upload Invoices</button>
      {message && <p>{message}</p>}

      <h2>Processed Invoices</h2>
      {processedInvoices.length === 0 ? (
        <p>No invoices processed yet. Upload some PDFs!</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Filename</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Status</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Invoice No.</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Vendor</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total Amount</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Type</th>
              <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Error</th>
            </tr>
          </thead>
          <tbody>
            {processedInvoices.map((invoice) => (
              <tr key={invoice.id} style={{ backgroundColor: invoice.status === 'failed' ? '#ffe0e0' : (invoice.status === 'processed' ? '#e0ffe0' : '#e0e0ff') }}>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{invoice.filename}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{invoice.status}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{invoice.extracted_data?.invoice_number || 'N/A'}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{invoice.extracted_data?.vendor_name || 'N/A'}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                  {invoice.extracted_data?.total_amount !== undefined && invoice.extracted_data?.total_amount !== null
                    ? `${invoice.extracted_data.total_amount.toFixed(2)} ${invoice.extracted_data.currency || ''}`
                    : 'N/A'}
                </td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{invoice.extracted_data?.invoice_type || 'N/A'}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px', color: 'red' }}>{invoice.error_message || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}