import { api } from '@/utils/api'

// Types
export interface Document {
  id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  is_active: boolean
  project_id: number
  processed: boolean
  chunks: DocumentChunk[]
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: number
  chunk_index: number
  content: string
  created_at: string
}

export interface UploadDocumentRequest {
  project_id: number
  file: File
}

export interface UpdateDocumentRequest {
  is_active?: boolean
}

export interface DocumentProcessingStatus {
  document_id: number
  filename: string
  processed: boolean
  chunk_count: number
  file_size: number
  created_at: string
}

// Documents API
export const documentsApi = {
  // Document operations
  getDocumentsByProject: (projectId: number) =>
    api.get(`/api/projects/${projectId}/documents`),

  getDocument: (documentId: number) => 
    api.get(`/api/documents/${documentId}`),

  uploadDocument: (data: UploadDocumentRequest) => {
    const formData = new FormData()
    formData.append('file', data.file)
    
    return api.post(`/api/projects/${data.project_id}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  updateDocument: (documentId: number, data: UpdateDocumentRequest) =>
    api.put(`/api/documents/${documentId}`, data),

  deleteDocument: (documentId: number) =>
    api.delete(`/api/documents/${documentId}`),

  // Document chunks
  getDocumentChunks: (documentId: number) =>
    api.get(`/api/documents/${documentId}/chunks`),

  // Document processing
  reprocessDocument: (documentId: number) =>
    api.post(`/api/documents/${documentId}/reprocess`),
  
  getProcessingStatus: (projectId: number) =>
    api.get(`/api/projects/${projectId}/documents/status`),

  // Batch operations
  bulkUpdateDocuments: (projectId: number, documentIds: number[], data: UpdateDocumentRequest) =>
    api.put(`/api/projects/${projectId}/documents/bulk`, {
      document_ids: documentIds,
      ...data
    }),
}

export default documentsApi