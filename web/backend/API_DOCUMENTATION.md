# IGCSE Biology Database API Documentation

This API provides endpoints to query the IGCSE Biology question database stored in MongoDB.

## Database Structure

- Database: `igcse-biology-0610`
- Collections: Various paper collections like `0610_m15_qp_12_mcq`, `0610_m15_qp_22_sq`, etc.
- Each document contains questions with nested subquestions and syllabus information

## Setup Instructions

1. **Install Dependencies**

   ```bash
   cd frontend
   npm install
   ```

2. **Environment Configuration**
   Make sure `.env` file contains:

   ```
   MONGO_URI=mongodb://120.25.192.109:27017
   ```

3. **Start Server**
   ```bash
   npm start
   # or for development
   npm run dev
   ```

## API Endpoints

### 1. Health Check

**GET** `/api/health`

Returns server status and timestamp.

**Response:**

```json
{
  "success": true,
  "message": "Server is running",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 2. Get All Papers

**GET** `/api/papers`

Returns list of all available papers (collections).

**Response:**

```json
{
  "success": true,
  "data": ["0610_m15_qp_12_mcq", "0610_m15_qp_22_sq", ...],
  "count": 25
}
```

### 3. Get Syllabus List

**GET** `/api/syllabus`

Returns unique syllabus topics from all questions.

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "number": "1.3",
      "title": "1.3 Features of organisms"
    },
    {
      "number": "6.2",
      "title": "6.2 Leaf structure"
    }
  ],
  "count": 50
}
```

### 4. Get Questions by Syllabus

**GET** `/api/questions/by-syllabus/:syllabusNumber`

Returns questions filtered by syllabus number.

**Parameters:**

- `syllabusNumber` (required): Syllabus number (e.g., "1.3", "6.2")

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)
- `paper` (optional): Specific paper to search in

**Example:** `GET /api/questions/by-syllabus/1.3?page=1&limit=5&paper=0610_m15_qp_22_sq`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "number": 1,
      "text": "Fig. 1.1 shows six different cells...",
      "subquestions": [...],
      "paper": "0610_m15_qp_22_sq"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 10,
    "totalItems": 95,
    "itemsPerPage": 10
  }
}
```

### 5. Get Questions by Paper

**GET** `/api/questions/by-paper/:paperName`

Returns all questions from a specific paper.

**Parameters:**

- `paperName` (required): Paper collection name

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)

**Example:** `GET /api/questions/by-paper/0610_m15_qp_22_sq?page=1&limit=5`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "number": 1,
      "text": "Fig. 1.1 shows six different cells...",
      "subquestions": [...]
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 5,
    "totalItems": 45,
    "itemsPerPage": 10
  }
}
```

### 6. Get Specific Question

**GET** `/api/questions/:questionNumber`

Returns a specific question by number from a paper.

**Parameters:**

- `questionNumber` (required): Question number

**Query Parameters:**

- `paper` (required): Paper collection name

**Example:** `GET /api/questions/1?paper=0610_m15_qp_22_sq`

**Response:**

```json
{
  "success": true,
  "data": {
    "number": 1,
    "text": "Fig. 1.1 shows six different cells...",
    "subquestions": [
      {
        "number": "a",
        "text": "(a) Table 1.1 shows a key...",
        "syllabus": {
          "number": "1.3",
          "title": "1.3 Features of organisms"
        }
      }
    ]
  }
}
```

### 7. Search Questions

**POST** `/api/questions/search`

Search questions by text content with optional filters.

**Request Body:**

```json
{
  "query": "cell wall",
  "papers": ["0610_m15_qp_22_sq"],
  "syllabusNumbers": ["1.3", "6.2"],
  "page": 1,
  "limit": 10
}
```

**Parameters:**

- `query` (required): Search term
- `papers` (optional): Array of paper names to search in
- `syllabusNumbers` (optional): Array of syllabus numbers to filter by
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 10)

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "number": 1,
      "text": "Question containing 'cell wall'...",
      "paper": "0610_m15_qp_22_sq"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 3,
    "totalItems": 28,
    "itemsPerPage": 10
  }
}
```

### 8. Get Database Statistics

**GET** `/api/stats`

Returns database statistics including paper counts and question counts.

**Response:**

```json
{
  "success": true,
  "data": {
    "totalPapers": 25,
    "totalQuestions": 1250,
    "paperStats": [
      {
        "paper": "0610_m15_qp_22_sq",
        "questionCount": 50
      }
    ]
  }
}
```

### 9. Filter Questions (Unified)

**POST** `/api/questions/filter`

Filter questions by any combination of syllabus numbers, papers, question types, and paper types, with pagination.

**Request Body:**

```json
{
  "syllabusNumbers": ["1.3", "6.2"],
  "papers": ["0610_m15_qp_22_sq"],
  "questionTypes": ["sq", "mcq"],
  "paperTypes": ["paper1", "2", "paper3"],
  "page": 1,
  "limit": 10
}
```

**Parameters:**

- `syllabusNumbers` (optional, string[]): Syllabus numbers to include (e.g., "1.3", "6.2").
- `papers` (optional, string[]): Specific collection names to search in.
- `questionTypes` (optional, string[]): Question type suffixes: "sq", "mcq".
- `paperTypes` (optional, string[]): Paper types, accepts "paper1"/"1", "paper2"/"2", etc.
- `page` (optional, number): Page number (default: 1).
- `limit` (optional, number): Items per page (default: 10, max: 100).

**Notes:**

- `questionTypes` filters by collection suffix, e.g., `_sq` or `_mcq`.
- `paperTypes` maps to the first digit in the two-digit code after `_qp_` in the collection name.  
  Example: `0610_m15_qp_12_mcq` → paper type "1"; `0610_m15_qp_22_sq` → paper type "2".  
  Accepts either "paper1" or "1".
- If `papers` is provided, it serves as the base set and type filters still apply.

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "number": 1,
      "text": "Question text...",
      "subquestions": [...],
      "paper": "0610_m15_qp_22_sq"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 3,
    "totalItems": 28,
    "itemsPerPage": 10
  }
}
```

**Example (fetch):**

```javascript
fetch("/api/questions/filter", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    syllabusNumbers: ["1.3"],
    questionTypes: ["sq"],
    paperTypes: ["paper2"],
    page: 1,
    limit: 5,
  }),
})
  .then((r) => r.json())
  .then(console.log);
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "details": "Detailed error message"
}
```

## Usage Examples

### Frontend Integration

```javascript
// Get syllabus list
fetch("/api/syllabus")
  .then((response) => response.json())
  .then((data) => console.log(data.data));

// Search questions by syllabus
fetch("/api/questions/by-syllabus/1.3?page=1&limit=5")
  .then((response) => response.json())
  .then((data) => console.log(data.data));

// Search questions by text
fetch("/api/questions/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "photosynthesis",
    syllabusNumbers: ["6.2"],
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data.data));
```

## Features

- **Pagination**: All list endpoints support pagination
- **Cross-collection search**: Search across all papers or specific papers
- **Flexible filtering**: Filter by syllabus numbers, papers, or text content
- **Nested data handling**: Searches both main questions and subquestions
- **Error handling**: Comprehensive error responses with details
- **CORS enabled**: Ready for frontend integration
- **Health monitoring**: Health check endpoint for monitoring

## Notes

- All responses include a `success` field indicating the operation status
- Pagination information is included when applicable
- The server connects to MongoDB on startup and handles connection errors gracefully
- All text searches are case-insensitive
