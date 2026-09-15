export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export type StyleScore = {
  name: string;
  score: number;
};

export type StyleDna = {
  styles: StyleScore[];
  colors: string[];
  garments: string[];
  fits: string[];
  patterns: string[];
  materials: string[];
  traits: string[];
};

export type AnalyzeResponse = {
  profile_id: number;
  style_dna: StyleDna;
  sources_processed: number;
  sources_failed: number;
};

export type ProfileResponse = {
  id: number;
  name: string;
  style_dna: StyleDna;
};

export type RecommendationItem = {
  id: number;
  title: string;
  image_url: string;
  pinterest_url: string;
  description: string | null;
  match_score: number;
  match_reason: string;
  position: number;
};

export type GenerateResponse = {
  id: number;
  occasion: string;
  search_intent: string;
  provider_status: 'ok' | 'degraded' | 'failed';
  recommendations: RecommendationItem[];
};

export type FeedbackReaction = 'like' | 'maybe' | 'dislike';

export type FeedbackResponse = {
  status: string;
  result_id: number;
  reaction: FeedbackReaction;
};

export type HealthResponse = {
  status: 'ok';
};

export type InspirationImage = {
  uri: string;
  fileName?: string | null;
  mimeType?: string | null;
};

export function getApiBaseUrl(): string {
  const raw = process.env.EXPO_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, '');
  if (!raw) {
    throw new Error(
      'EXPO_PUBLIC_API_BASE_URL is required. For Expo Go on a physical phone, set it to your computer LAN IP, for example http://192.168.1.42:8000',
    );
  }
  return raw;
}

export function getDevelopmentUserId(): number {
  const rawUserId = process.env.EXPO_PUBLIC_DEV_USER_ID?.trim();
  if (!rawUserId) {
    throw new Error(
      'EXPO_PUBLIC_DEV_USER_ID is required for development. Set it to an existing backend user ID.',
    );
  }

  const userId = Number(rawUserId);
  if (!Number.isInteger(userId) || userId <= 0) {
    throw new Error('EXPO_PUBLIC_DEV_USER_ID must be a positive integer.');
  }

  return userId;
}

export async function getHealth(): Promise<HealthResponse> {
  const data = await requestJson('/health');
  if (!isHealthResponse(data)) {
    throw new ApiRequestError('Health check returned an unexpected response.');
  }
  return data;
}

function inspirationFileName(image: InspirationImage, index: number): string {
  const fileName = image.fileName?.trim();
  if (fileName) {
    return fileName;
  }
  const mime = image.mimeType ?? '';
  const extension = mime.includes('png') ? 'png' : mime.includes('webp') ? 'webp' : 'jpg';
  return `inspiration-${index + 1}.${extension}`;
}

async function appendInspirationImage(
  formData: FormData,
  image: InspirationImage,
  index: number,
): Promise<void> {
  const name = inspirationFileName(image, index);
  const mimeType = image.mimeType?.trim() || 'image/jpeg';

  let blob: Blob;
  try {
    const response = await fetch(image.uri);
    if (!response.ok) {
      throw new Error('unreadable');
    }
    blob = await response.blob();
  } catch {
    throw new ApiRequestError(`Could not read inspiration image ${name}.`);
  }

  const type = blob.type && blob.type !== 'application/octet-stream' ? blob.type : mimeType;

  // Expo 52+ uses WHATWG FormData. The old RN `{ uri, name, type }` object is
  // stringified to "[object Object]" and FastAPI 422s (Expected UploadFile).
  if (typeof File === 'function') {
    formData.append('images', new File([blob], name, { type }));
    return;
  }

  formData.append('images', blob, name);
}

export async function analyzeStyle(
  images: InspirationImage[],
  userId: number,
  inspirationUrls: string[] = [],
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('user_id', String(userId));

  for (const [index, image] of images.entries()) {
    await appendInspirationImage(formData, image, index);
  }

  for (const url of inspirationUrls) {
    const flickrUrl = url.trim();
    if (flickrUrl) {
      formData.append('inspiration_urls', flickrUrl);
    }
  }

  const data = await requestJson('/style/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!isAnalyzeResponse(data)) {
    throw new ApiRequestError('Style analysis returned an unexpected response.');
  }

  return data;
}

export async function getProfile(userId: number): Promise<ProfileResponse> {
  const data = await requestJson(`/profile/${userId}`);
  if (!isProfileResponse(data)) {
    throw new ApiRequestError('Profile lookup returned an unexpected response.');
  }
  return data;
}

export async function generateOutfit(
  occasion: string,
  userId: number,
): Promise<GenerateResponse> {
  const data = await requestJson('/outfits/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, occasion }),
  });

  if (!isGenerateResponse(data)) {
    throw new ApiRequestError('Outfit generation returned an unexpected response.');
  }

  return data;
}

export async function submitFeedback(
  outfitId: number,
  resultId: number,
  reaction: FeedbackReaction,
): Promise<FeedbackResponse> {
  const data = await requestJson(`/outfits/${outfitId}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ result_id: resultId, reaction }),
  });

  if (!isFeedbackResponse(data)) {
    throw new ApiRequestError('Feedback submit returned an unexpected response.');
  }

  return data;
}

async function requestJson(path: string, init?: RequestInit): Promise<unknown> {
  const baseUrl = getApiBaseUrl();
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch {
    throw new ApiRequestError(
      `Could not reach Style DNA at ${baseUrl}. On a physical phone, EXPO_PUBLIC_API_BASE_URL must be your computer LAN IP, not localhost.`,
    );
  }

  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiRequestError(formatHttpError(response.status, data), response.status);
  }

  return data;
}

export function isMissingProfileError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.status === 404 &&
    (error.message.toLowerCase().includes('style profile') ||
      error.message.toLowerCase().includes('no style dna'))
  );
}

function formatHttpError(status: number, data: unknown): string {
  const detail = getErrorDetail(data);
  const lowered = detail.toLowerCase();
  if (status === 404 && lowered.includes('does not exist')) {
    return 'Development user does not exist in the backend database. Check EXPO_PUBLIC_DEV_USER_ID.';
  }
  if (status === 404 && lowered.includes('style profile')) {
    return detail || 'No Style DNA profile exists yet. Analyze inspiration first.';
  }
  return detail || `Request failed with status ${status}.`;
}

function getErrorDetail(data: unknown): string {
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const detail = data.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => JSON.stringify(item)).join(', ');
    }
  }
  return '';
}

function isAnalyzeResponse(data: unknown): data is AnalyzeResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const response = data as Record<string, unknown>;
  return (
    Number.isInteger(response.profile_id) &&
    isStyleDna(response.style_dna) &&
    isNonNegativeInteger(response.sources_processed) &&
    isNonNegativeInteger(response.sources_failed)
  );
}

function isProfileResponse(data: unknown): data is ProfileResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const response = data as Record<string, unknown>;
  return (
    Number.isInteger(response.id) &&
    typeof response.name === 'string' &&
    isStyleDna(response.style_dna)
  );
}

function isStyleDna(data: unknown): data is StyleDna {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const styleDna = data as Record<string, unknown>;
  return (
    isStyleScores(styleDna.styles) &&
    isStringArray(styleDna.colors) &&
    isStringArray(styleDna.garments) &&
    isStringArray(styleDna.fits) &&
    isStringArray(styleDna.patterns) &&
    isStringArray(styleDna.materials) &&
    isStringArray(styleDna.traits)
  );
}

function isStyleScores(data: unknown): data is StyleScore[] {
  return (
    Array.isArray(data) &&
    data.every(
      (item) =>
        typeof item === 'object' &&
        item !== null &&
        typeof item.name === 'string' &&
        typeof item.score === 'number',
    )
  );
}

function isGenerateResponse(data: unknown): data is GenerateResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const response = data as Record<string, unknown>;
  return (
    Number.isInteger(response.id) &&
    typeof response.occasion === 'string' &&
    typeof response.search_intent === 'string' &&
    isProviderStatus(response.provider_status) &&
    isRecommendationArray(response.recommendations)
  );
}

function isProviderStatus(data: unknown): data is GenerateResponse['provider_status'] {
  return data === 'ok' || data === 'degraded' || data === 'failed';
}

function isRecommendationArray(data: unknown): data is RecommendationItem[] {
  return Array.isArray(data) && data.every(isRecommendationItem);
}

function isRecommendationItem(data: unknown): data is RecommendationItem {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const item = data as Record<string, unknown>;
  return (
    Number.isInteger(item.id) &&
    typeof item.title === 'string' &&
    typeof item.image_url === 'string' &&
    typeof item.pinterest_url === 'string' &&
    (typeof item.description === 'string' || item.description === null) &&
    typeof item.match_score === 'number' &&
    typeof item.match_reason === 'string' &&
    isNonNegativeInteger(item.position)
  );
}

function isFeedbackResponse(data: unknown): data is FeedbackResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const response = data as Record<string, unknown>;
  return (
    typeof response.status === 'string' &&
    Number.isInteger(response.result_id) &&
    (response.reaction === 'like' || response.reaction === 'maybe' || response.reaction === 'dislike')
  );
}

function isHealthResponse(data: unknown): data is HealthResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'status' in data &&
    data.status === 'ok'
  );
}

function isStringArray(data: unknown): data is string[] {
  return Array.isArray(data) && data.every((item) => typeof item === 'string');
}

function isNonNegativeInteger(data: unknown): data is number {
  return typeof data === 'number' && Number.isInteger(data) && data >= 0;
}
