export interface InvoiceItem {
  platform: string;
  filename: string;
  invoice_number: string;
  invoice_id: string;
  invoice_type: string;
  line_number: number;
  description: string;
  amount: number;
  total: number;
  agency?: string | null;
  project_id?: string | null;
  project_name?: string | null;
  objective?: string | null;
  period?: string | null;
  campaign_id?: string | null;
}

export interface InvoiceFile {
  platform: string;
  invoice_type: string;
  total_amount: number;
  items_count: number;
  items: InvoiceItem[];
}

export interface InvoiceReport {
  generated_at: string;
  invoice_set?: string;
  total_files: number;
  summary: {
    by_platform: {
      [platform: string]: {
        total_amount: number;
        total_items: number;
        files: number;
        average_items_per_file: number;
      };
    };
    overall: {
      total_amount: number;
      total_items: number;
      files_processed: number;
    };
  };
  files: {
    [filename: string]: InvoiceFile;
  };
}

export interface ProcessingResult {
  success: boolean;
  message: string;
  data?: InvoiceReport;
  error?: string;
}