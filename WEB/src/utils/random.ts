export function randomId(prefix = 'el_') {
  const pool = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = prefix;
  for (let i = 0; i < 12; i += 1) {
    result += pool[Math.floor(Math.random() * pool.length)];
  }
  return result;
}

export function randomStr(length = 12) {
  const pool = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < length; i += 1) {
    result += pool[Math.floor(Math.random() * pool.length)];
  }
  return result;
}

export function shuffle<T>(items: T[]) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function downloadBlob(filename: string, content: string | Blob, mimeType = 'application/octet-stream') {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Delay revoke so the browser can start the download pipeline
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Fetch a static URL and force a file download (triggers Save As when browser asks for location). */
export async function downloadUrl(url: string, filename: string) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }
  const data = await response.blob();
  // Use octet-stream so the browser treats it as a download, not inline preview
  downloadBlob(filename, new Blob([data], { type: 'application/octet-stream' }));
}

