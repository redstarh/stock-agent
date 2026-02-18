import { http, HttpResponse } from 'msw';
import { mockNewsTop, mockNewsLatest, mockNewsScore, mockStockTimeline, mockThemeStrength, mockPrediction } from './data';

export const handlers = [
  http.get('/api/v1/news/top', ({ request }) => {
    const url = new URL(request.url);
    const market = url.searchParams.get('market') || 'KR';
    return HttpResponse.json(mockNewsTop(market));
  }),
  http.get('/api/v1/news/latest', () => HttpResponse.json(mockNewsLatest())),
  http.get('/api/v1/news/score', () => HttpResponse.json(mockNewsScore())),
  http.get('/api/v1/stocks/:code/timeline', ({ params }) =>
    HttpResponse.json(mockStockTimeline(params.code as string))
  ),
  http.get('/api/v1/stocks/:code/prediction', ({ params }) => {
    const data = mockPrediction(params.code as string);
    if (!data) {
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json(data);
  }),
  http.get('/api/v1/theme/strength', () => HttpResponse.json(mockThemeStrength())),
  http.get('/health', () => HttpResponse.json({ status: 'ok', version: '0.1.0' })),
];
