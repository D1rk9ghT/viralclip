import { auth } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface Project {
  id: string;
  title: string;
  status: string;
  progress_percent: number;
  error_message?: string;
}

class ApiClient {
  private async getHeaders(): Promise<HeadersInit> {
    const user = auth.currentUser;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (user) {
      const token = await user.getIdToken();
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  async getProjects(): Promise<Project[]> {
    const headers = await this.getHeaders();
    const response = await fetch(`${API_URL}/api/v1/projects`, {
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch projects');
    }

    return response.json();
  }

  async processVideo(url: string): Promise<{ project_id: string; status: string }> {
    const headers = await this.getHeaders();
    const response = await fetch(`${API_URL}/api/v1/process`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail || 'Failed to process video');
    }

    return response.json();
  }
}

export const api = new ApiClient();
