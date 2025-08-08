import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudArrowUpIcon } from './icons'

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  isProcessing: boolean
}

export default function FileUpload({ onFilesSelected, isProcessing }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFilesSelected(acceptedFiles)
  }, [onFilesSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    disabled: isProcessing
  })

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'}
        ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <CloudArrowUpIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
      {isDragActive ? (
        <p className="text-lg font-medium text-primary-600">Drop the PDF files here...</p>
      ) : (
        <>
          <p className="text-lg font-medium text-gray-700 mb-2">
            Drag & drop invoice PDF files here
          </p>
          <p className="text-sm text-gray-500">
            or click to select files
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Supports Facebook, Google, and TikTok invoices
          </p>
        </>
      )}
    </div>
  )
}