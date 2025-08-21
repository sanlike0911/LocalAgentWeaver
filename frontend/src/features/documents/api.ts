import { api } from '@/utils/api'

// Types
export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  is_active: boolean
  project_id: string
  upload_date: string
  chunk_count?: number
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: string
  document_id: string
  content: string
  chunk_index: number
  embedding_vector?: number[]
  created_at: string
}

export interface UploadDocumentRequest {
  project_id: number
  file: File
}

export interface UpdateDocumentRequest {
  is_active?: boolean
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
    formData.append('project_id', data.project_id.toString())
    
    return api.post('/api/documents/upload', formData, {
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

  // Batch operations
  bulkUpdateDocuments: (projectId: number, documentIds: number[], data: UpdateDocumentRequest) =>
    api.put(`/api/projects/${projectId}/documents/bulk`, {
      document_ids: documentIds,
      ...data
    }),
}

export default documentsApi