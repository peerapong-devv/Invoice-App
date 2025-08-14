import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { path } = req.query;
  const targetPath = Array.isArray(path) ? path.join('/') : path;
  
  const targetUrl = `https://peepong.pythonanywhere.com/api/${targetPath}`;
  
  try {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const options: RequestInit = {
      method: req.method,
      headers,
    };

    // Forward body for POST requests
    if (req.method === 'POST' && req.body) {
      // Handle FormData for file uploads
      if (req.headers['content-type']?.includes('multipart/form-data')) {
        // For file uploads, we need to handle differently
        // This is a simplified version - you may need to adjust based on your needs
        return res.status(200).json({ 
          message: 'File upload endpoint - please use direct upload to PythonAnywhere' 
        });
      } else {
        options.body = JSON.stringify(req.body);
      }
    }

    const response = await fetch(targetUrl, options);
    const data = await response.json();
    
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(500).json({ error: 'Failed to connect to backend', details: error });
  }
}