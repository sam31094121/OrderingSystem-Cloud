# 餐廳點餐系統 (Restaurant Ordering System)

## 專案概述 (Overview)

這是一個即時餐廳點餐系統，以網頁應用程式的形式建置。系統讓服務員透過點餐介面接受顧客訂單，同時廚房人員可以透過廚房顯示系統即時接收和處理訂單。應用程式強調服務員和廚房介面之間的即時同步，確保訂單立即傳達，無需手動重新整理頁面。

**語言 (Language)**: 完整繁體中文介面 (Full Traditional Chinese Interface)

系統服務兩種主要用戶角色：
- **服務員 (Waiters)**: 瀏覽菜單項目、建立訂單並調整數量、新增備註、送單至廚房
- **廚房人員 (Kitchen Staff)**: 即時查看新訂單、更新訂單狀態（待處理→已接單→烹調中→已完成→已送達）、通知服務員進度

## 使用者偏好設定 (User Preferences)

- **介面語言**: 繁體中文 (Traditional Chinese)
- **溝通風格**: 簡單易懂的日常用語

## System Architecture

### Frontend Architecture

**Multi-Page Application (MPA) with Real-Time Updates**
- Three distinct HTML pages served by Flask templates: home page (role selection), waiter interface, and kitchen display
- Bootstrap 5 for responsive UI components and styling
- Vanilla JavaScript for client-side logic without heavy framework dependencies
- Socket.IO client for bidirectional real-time communication

**Rationale**: The MPA approach suits this use case because each role has a distinct, focused interface. Using server-rendered templates simplifies deployment and reduces complexity while still achieving real-time capabilities through WebSocket integration.

**購物車模式 (Shopping Cart Pattern - Waiter Interface)**
- 客戶端購物車管理，儲存於 JavaScript 記憶體
- 動態菜單渲染，依類別組織（主餐、沙拉、配菜、飲料、甜點）
- 送單前即時總計計算和訂單建立

**狀態篩選系統 (Status Filter System - Kitchen Interface)**
- 客戶端訂單顯示篩選（全部訂單、待處理、烹調中、已完成）
- 即時訂單列表更新，具視覺化狀態指標
- 新訂單通知系統（聲音提示）

### Backend Architecture

**Flask Web Framework with Socket.IO**
- Flask handles HTTP routes for serving pages and RESTful API endpoints
- Flask-SocketIO provides WebSocket server for real-time bidirectional communication
- CORS enabled for potential cross-origin requests

**Rationale**: Flask was chosen for its simplicity and Python ecosystem. The combination with Socket.IO allows for both traditional request-response patterns (menu loading, order submission) and real-time push notifications (order status updates, new order alerts). This hybrid approach provides flexibility without unnecessary complexity.

**API Design**
- RESTful endpoints for data retrieval (GET /api/menu, GET /api/orders)
- WebSocket events for real-time synchronization:
  - `new_order`: Broadcasted when waiter submits order
  - `order_updated`: Broadcasted when kitchen updates order status
  - Bidirectional communication enables instant UI updates on all connected clients

**Session Management**
- Secret key configuration via environment variable with fallback
- Session security not prioritized per requirements (internal, limited-use system)

### Data Storage

**SQLite Database**
- Lightweight, serverless, file-based relational database
- Two main tables:
  - `menu_items`: Stores dish information (name, price, description, category, availability)
  - `orders`: Stores order details (order number, items as JSON text, total amount, status, notes, timestamps)

**Rationale**: SQLite eliminates the need for separate database server setup, making deployment simpler. It's sufficient for the expected load of a single restaurant. The schema uses SQLite's built-in features like autoincrement IDs and timestamp defaults. Order items are stored as JSON text to maintain flexibility without requiring a complex relational schema for order line items.

**Database Initialization**
- Conditional initialization that checks for existing database file
- Sample menu data seeded on first run
- Row factory configured for dictionary-like access to query results

**Design Trade-offs**:
- **Pros**: Zero configuration, portable single-file database, adequate performance for small-scale use
- **Cons**: Limited concurrent write operations, no built-in replication, JSON text storage for order items isn't normalized (but simplifies queries for this use case)

### Real-Time Communication Layer

**WebSocket Architecture via Socket.IO**
- Persistent bidirectional connections between clients and server
- Event-driven message passing for order state changes
- Broadcast pattern to notify all connected clients of updates

**Rationale**: WebSockets were chosen over polling to achieve millisecond-level synchronization as specified in requirements. Socket.IO provides automatic reconnection, fallback mechanisms, and simplified event-based programming model compared to raw WebSockets.

**Event Flow**:
1. Waiter submits order → Server persists to database → Server emits `new_order` event → Kitchen displays immediately
2. Kitchen updates status → Server updates database → Server emits `order_updated` event → Waiter sees status change

### 訂單狀態流程 (Order Status Workflow)

**狀態進程**
- `pending` (待處理): 服務員送單後的初始狀態
- `received` (已接單): 廚房確認接收訂單
- `cooking` (烹調中): 訂單正在準備中
- `ready` (已完成): 食物準備完成，等待送餐
- `completed` (已送達): 訂單已送達顧客

**設計理念**: 此流程反映典型餐廳作業流程，並在外場和廚房之間提供清晰的溝通。狀態翻譯在客戶端處理，所有訂單狀態在使用者介面顯示為繁體中文。

## External Dependencies

### Third-Party Libraries

**Python Backend**
- `Flask`: Web application framework for routing and request handling
- `Flask-SocketIO`: WebSocket support for real-time features
- `Flask-CORS`: Cross-Origin Resource Sharing support
- Standard library: `sqlite3` for database operations, `json` for data serialization, `datetime` for timestamps

**Frontend JavaScript**
- `Socket.IO Client`: WebSocket client library for real-time communication (loaded via CDN)
- `Bootstrap 5`: CSS framework for responsive UI components (loaded via CDN)

### Database

**SQLite**
- No external database service required
- Database file (`restaurant.db`) stored locally in application directory
- Connection pooling handled through simple `get_db()` function with row factory

### Deployment Considerations

**Cloud Service Requirements**
- Application designed for cloud deployment (mentioned: free cloud service required)
- Environment variable support for `SESSION_SECRET` configuration
- CORS configuration allows deployment flexibility (currently set to wildcard)
- No static IP or DNS requirements explicitly defined

**Potential Hosting Platforms** (not explicitly configured):
- Replit, Heroku, Railway, Render, or similar PaaS providers
- Requirements: Python runtime, persistent file storage for SQLite, WebSocket support

## 部署說明 (Deployment Instructions)

**如何在 Replit 上運行**
1. 點擊 Replit 介面上方的 **Run** 按鈕
2. 系統會自動初始化資料庫並載入繁體中文菜單範例
3. 在新視窗中開啟應用程式
4. 選擇角色：
   - **服務員點餐系統**: 用於接受點餐
   - **廚房顯示系統**: 用於廚房接單和處理

**即時測試流程**
1. 在一個瀏覽器視窗中開啟「服務員點餐系統」
2. 在另一個瀏覽器視窗中開啟「廚房顯示系統」
3. 在服務員介面中選擇菜單項目並送單
4. 觀察訂單即時出現在廚房顯示系統（會有聲音提示）
5. 在廚房系統中更新訂單狀態（接單→開始烹調→標記完成→訂單送達）

## 最近更新 (Recent Changes)

- **2025-10-18**: 完整繁體中文本地化
  - 所有介面文字轉換為繁體中文
  - 菜單項目使用繁體中文（漢堡、披薩、義大利麵等）
  - 訂單狀態標籤翻譯（待處理、已接單、烹調中、已完成、已送達）
  - 通知訊息完全繁體中文化
  - JavaScript 狀態代碼映射，確保無英文顯示
  - 即時同步功能已驗證正常運作