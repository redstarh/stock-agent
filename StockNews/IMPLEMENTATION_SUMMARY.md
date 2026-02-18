# Redis Pub/Sub → WebSocket Breaking News Pipeline Implementation

## Overview
Implemented a complete real-time breaking news notification system that publishes high-score news events (score >= 80) from the backend to frontend clients via Redis Pub/Sub and WebSocket.

## Components Implemented

### Backend

#### 1. Enhanced Redis Pub/Sub Module (`app/core/pubsub.py`)
- **`publish_news_event()`**: Publishes NewsEvent objects with score >= 80 to Redis channels
- **`subscribe_and_broadcast()`**: Async function that subscribes to Redis channels and broadcasts to WebSocket
- **Channel naming**: `news_breaking_kr` and `news_breaking_us`
- **Message format**: JSON with fields: stock_code, stock_name, title, theme, sentiment, news_score, market, published_at

#### 2. WebSocket Enhancement (`app/api/websocket.py`)
- **Redis subscriber**: Automatically starts when first client connects
- **Background task**: Subscribes to both KR and US channels
- **Broadcasting**: Relays breaking news to all connected WebSocket clients
- **Lifecycle management**: Stops Redis subscription when last client disconnects
- **Message types**: `breaking_news`, `score_update`, `connected`, `pong`

### Frontend

#### 1. Enhanced useWebSocket Hook (`src/hooks/useWebSocket.ts`)
- **Notification management**: Stores last 10 notifications with read/unread state
- **Callback support**: Optional `onBreakingNews` callback for Toast integration
- **State management**:
  - `notifications`: Array of Notification objects
  - `unreadCount`: Number of unread notifications
  - `markAsRead(id)`: Mark single notification as read
  - `markAllAsRead()`: Mark all as read
  - `clearNotifications()`: Clear all notifications

#### 2. Enhanced NotificationBell Component (`src/components/common/NotificationBell.tsx`)
- **Unread badge**: Shows count of unread notifications
- **Dropdown UI**: Shows last 10 notifications with timestamps
- **Read/Unread states**: Visual distinction (blue background for unread)
- **Actions**: "모두 읽음" and "전체 삭제" buttons
- **Click handling**: Marks notification as read when clicked

#### 3. App Integration (`src/App.tsx`)
- **WebSocket connection**: Connects to `ws://localhost:8000/ws/news`
- **Toast integration**: Shows breaking news as Toast notifications
- **Props threading**: Passes notification state through Layout → Header → NotificationBell

#### 4. Type Definitions (`src/types/api.ts`)
- **`BreakingNewsData`**: Interface for breaking news payload
- **`Notification`**: Interface with id, message, timestamp, read status

## Data Flow

```
Scoring Engine (score >= 80)
    ↓
publish_news_event() → Redis Pub/Sub (news_breaking_{kr|us})
    ↓
WebSocket subscribe_and_broadcast() (background task)
    ↓
WebSocket.broadcast() → All connected clients
    ↓
Frontend useWebSocket hook
    ↓
├─ Toast notification (popup)
└─ NotificationBell (persistent badge + history)
```

## Tests

### Backend Tests
- **`tests/unit/test_pubsub_enhanced.py`** (5 tests)
  - NewsEvent publishing with all fields
  - Threshold enforcement (< 80 not published)
  - Market-specific channels
  - Optional field handling

- **`tests/integration/test_websocket_broadcast.py`** (7 tests)
  - Broadcasting to multiple clients
  - Disconnected client removal
  - Redis subscription integration
  - Connection management

- **`tests/integration/test_redis_pubsub.py`** (5 tests - existing, still passing)
  - Basic pub/sub functionality
  - Channel naming
  - Threshold logic

**Total: 17 backend tests, all passing**

### Frontend Tests
- **`tests/hooks/useWebSocket.test.ts`** (8 tests)
  - WebSocket connection
  - Breaking news notification creation
  - Callback invocation
  - Mark as read/unread functionality
  - Notification limit (max 10)

- **`tests/components/NotificationBell.test.tsx`** (4 tests)
  - Unread badge display
  - Dropdown functionality
  - Action buttons (mark all read, clear)
  - Notification click handling

- **Updated existing tests** (3 test files)
  - `tests/components/layout/Layout.test.tsx`
  - `tests/components/layout/Header.test.tsx`
  - Updated for new props signatures

**Total: 136 frontend tests, all passing**

## Configuration

### Environment Variables
- **Frontend**: `VITE_WS_URL` (default: `ws://localhost:8000/ws/news`)

### Constants
- **Breaking threshold**: 80.0 (defined in `app/core/pubsub.py`)
- **Max notifications**: 10 (defined in `src/hooks/useWebSocket.ts`)
- **Max WebSocket connections**: 100 (defined in `app/api/websocket.py`)

## Usage Example

### Backend: Publishing Breaking News
```python
from app.core.pubsub import publish_news_event
from app.core.redis import get_redis

# After scoring a news event
redis_client = get_redis()
if news_event.news_score >= 80:
    publish_news_event(redis_client, news_event, news_event.news_score)
```

### Frontend: Consuming Notifications
```tsx
const { notifications, unreadCount, markAsRead, markAllAsRead } =
  useWebSocket(WS_URL, (data) => {
    // Show toast for breaking news
    showToast(`${data.stock_name}: ${data.title}`);
  });
```

## Key Features

1. **Real-time**: Sub-second latency from scoring to frontend notification
2. **Scalable**: Redis Pub/Sub handles multiple backend instances
3. **Resilient**: WebSocket auto-reconnects on connection loss
4. **User-friendly**: Persistent notification history with read/unread tracking
5. **Tested**: Comprehensive unit and integration test coverage
6. **Type-safe**: Full TypeScript support on frontend

## Future Enhancements

1. **Persistence**: Store notifications in database for cross-device sync
2. **Filtering**: Allow users to filter by market, theme, or stock
3. **Sound/Desktop notifications**: Browser notification API integration
4. **Configurable threshold**: Allow users to set custom score thresholds
5. **Notification actions**: Quick actions (e.g., "View stock details")
