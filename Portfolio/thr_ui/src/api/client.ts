import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

export const api = axios.create({ baseURL: BASE });

export function buildFormData(fields: Record<string, unknown>): FormData {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) {
    if (v === undefined || v === null) continue;
    if (v instanceof File) fd.append(k, v);
    else if (v instanceof FileList) Array.from(v).forEach(f => fd.append(k, f));
    else if (Array.isArray(v)) v.forEach(item => fd.append(k, item instanceof File ? item : String(item)));
    else fd.append(k, String(v));
  }
  return fd;
}

export async function downloadBlob(url: string, data: FormData, filename: string) {
  const resp = await api.post(url, data, { responseType: 'blob' });
  const href = URL.createObjectURL(resp.data);
  const a = Object.assign(document.createElement('a'), { href, download: filename });
  a.click();
  URL.revokeObjectURL(href);
}
