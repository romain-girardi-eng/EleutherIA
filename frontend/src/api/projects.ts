import { apiClient } from './client';

// ── Types ────────────────────────────────────────────────────────────────────

export type ProjectStatus = 'active' | 'archived';

export type DocumentStatus = 'processing' | 'ready' | 'failed';

export interface ResearchProject {
  project_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface ProjectDocument {
  document_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  page_count: number | null;
  status: DocumentStatus;
  created_at: string;
}

export interface ProjectDetail extends ResearchProject {
  documents: ProjectDocument[];
}

export interface ProjectDocumentDetail extends ProjectDocument {
  extracted_text: string | null;
  page_texts: string[] | null;
  project_id: string;
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function listProjects(): Promise<ResearchProject[]> {
  const response = await apiClient.get<{ projects: ResearchProject[] }>('/api/projects');
  return response.data.projects;
}

export async function createProject(data: {
  name: string;
  description?: string;
}): Promise<ResearchProject> {
  const response = await apiClient.post<ResearchProject>('/api/projects', data);
  return response.data;
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  const response = await apiClient.get<ProjectDetail>(
    `/api/projects/${encodeURIComponent(projectId)}`
  );
  return response.data;
}

export async function updateProject(
  projectId: string,
  data: { name?: string; description?: string; status?: ProjectStatus }
): Promise<ResearchProject> {
  const response = await apiClient.put<ResearchProject>(
    `/api/projects/${encodeURIComponent(projectId)}`,
    data
  );
  return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/api/projects/${encodeURIComponent(projectId)}`);
}

export async function listDocuments(projectId: string): Promise<ProjectDocument[]> {
  const response = await apiClient.get<{ documents: ProjectDocument[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/documents`
  );
  return response.data.documents;
}

export async function uploadDocument(
  projectId: string,
  file: File,
  onProgress?: (ratio: number) => void
): Promise<ProjectDocument> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<ProjectDocument>(
    `/api/projects/${encodeURIComponent(projectId)}/documents`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event: { loaded: number; total?: number }) => {
        if (!onProgress) return;
        const total = event.total ?? file.size;
        if (!total) return;
        onProgress(Math.min(1, Math.max(0, event.loaded / total)));
      },
    }
  );
  return response.data;
}

export async function getDocument(documentId: string): Promise<ProjectDocumentDetail> {
  const response = await apiClient.get<ProjectDocumentDetail>(
    `/api/projects/documents/${encodeURIComponent(documentId)}`
  );
  return response.data;
}

export async function getDocumentFileBlob(documentId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `/api/projects/documents/${encodeURIComponent(documentId)}/file`,
    { responseType: 'blob' }
  );
  return response.data;
}

export async function deleteDocument(
  projectId: string,
  documentId: string
): Promise<void> {
  await apiClient.delete(
    `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}`
  );
}
