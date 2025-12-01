# IGCSE Biology API Documentation

A comprehensive REST API for querying IGCSE Biology questions and syllabus topics with advanced filtering, search, and pagination capabilities.

## Table of Contents

1. [Setup](#setup)
2. [API Endpoints](#api-endpoints)
3. [Data Models](#data-models)
4. [Usage Examples](#usage-examples)
5. [Error Handling](#error-handling)

## Setup

### Prerequisites

- Node.js (v16 or higher)
- MongoDB
- npm or pnpm

### Installation

```bash
# Install dependencies
pnpm install

# Import sample data
pnpm run import

# Start development server
pnpm run dev

# Start production server
pnpm start
```

### Environment Variables

Create a `.env` file with the following variables:

```env
MONGO_URI=mongodb://admin:password@host:port
PORT=3000
```

## API Endpoints

### Base URL

```
http://localhost:3000/api
```

### Health Check

#### GET /api/health

Check API status and database connection.

**Response:**

```json
{
  "status": "OK",
  "timestamp": "2023-01-01T00:00:00.000Z",
  "database": "Connected"
}
```

## Questions API

### GET /api/questions

Get questions with filtering and pagination.

**Query Parameters:**

- `page` (number, default: 1) - Page number
- `limit` (number, default: 20) - Items per page
- `paper_type` (string) - Question type: `mcq`, `sq`, `atp`, `as`, `a2`
- `year` (string) - Exam year: `2020`, `2021`, etc.
- `session` (string) - Exam session: `s20`, `w20`, `m20`, etc.
- `variant` (string) - Paper variant: `22`, `32`, etc.
- `syllabus` (string) - Syllabus topic number: `1.1`, `2.1`, etc.
- `topic` (string) - Topic tag
- `difficulty` (string) - Difficulty level: `easy`, `medium`, `hard`
- `search` (string) - Text search query
- `sort` (string, default: `number`) - Sort field
- `order` (string, default: `asc`) - Sort order: `asc`, `desc`

**Example Request:**

```
GET /api/questions?paper_type=mcq&year=2020&page=1&limit=10&search=photosynthesis
```

**Response:**

```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "_id": "...",
        "number": 1,
        "text": "Which diagram shows...",
        "options": ["A", "B", "C", "D"],
        "answer": "B",
        "image": "images/question1.png",
        "paper": "0610_s20_qp_22",
        "paper_type": "mcq",
        "year": "2020",
        "session": "s20",
        "variant": "22",
        "syllabus": {
          "number": "6.1",
          "title": "6.1 Photosynthesis",
          "content": ["..."]
        },
        "topics": ["6.1"],
        "keywords": ["photosynthesis", "chloroplast"],
        "difficulty": "medium"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_questions": 50,
      "questions_per_page": 10,
      "has_next": true,
      "has_previous": false
    },
    "filters": {
      "paper_type": "mcq",
      "year": "2020",
      "search": "photosynthesis"
    }
  }
}
```

### GET /api/questions/:id

Get a specific question by ID.

**Response:**

```json
{
  "success": true,
  "data": {
    "_id": "...",
    "number": 1,
    "text": "Question text..."
    // ... full question object
  }
}
```

### GET /api/questions/paper/:paper

Get all questions from a specific paper.

**Parameters:**

- `paper` - Paper code (e.g., `0610_s20_qp_22`)

**Query Parameters:**

- `page` (number, default: 1)
- `limit` (number, default: 50)

**Response:**

```json
{
  "success": true,
  "data": {
    "questions": [...],
    "paper": "0610_s20_qp_22",
    "total_questions": 40,
    "pagination": {...}
  }
}
```

### GET /api/questions/stats/overview

Get question statistics overview.

**Response:**

```json
{
  "success": true,
  "data": {
    "overview": {
      "total_questions": 89,
      "mcq_questions": 40,
      "sq_questions": 49
    },
    "stats": {
      "by_year": [{ "_id": "2020", "count": 89 }],
      "by_topic": [
        { "_id": "6.1", "count": 5 },
        { "_id": "1.1", "count": 3 }
      ],
      "by_paper_type": [
        { "_id": "mcq", "count": 40 },
        { "_id": "sq", "count": 49 }
      ]
    }
  }
}
```

### GET /api/questions/random

Get random questions with optional filtering.

**Query Parameters:**

- `count` (number, default: 10) - Number of questions
- `paper_type` (string) - Filter by question type
- `syllabus` (string) - Filter by syllabus topic
- `difficulty` (string) - Filter by difficulty
- `year` (string) - Filter by year

**Response:**

```json
{
  "success": true,
  "data": {
    "questions": [...],
    "count": 10,
    "filters": {...}
  }
}
```

### POST /api/questions

Create a new question (admin endpoint).

**Request Body:**

```json
{
  "number": 1,
  "text": "Question text...",
  "paper": "0610_s20_qp_22",
  "paper_type": "mcq",
  "options": ["A", "B", "C", "D"],
  "answer": "A",
  "syllabus": {
    "number": "1.1",
    "title": "1.1 Characteristics of living organisms",
    "content": [...]
  }
}
```

### POST /api/questions/bulk

Bulk import questions (admin endpoint).

**Request Body:**

```json
{
  "questions": [
    {...},
    {...}
  ]
}
```

## Syllabus API

### GET /api/syllabus

Get all syllabus topics with filtering.

**Query Parameters:**

- `page` (number, default: 1)
- `limit` (number, default: 50)
- `category` (string) - Filter by category
- `level` (string) - Filter by level: `core`, `supplement`, `both`
- `search` (string) - Text search

**Response:**

```json
{
  "success": true,
  "data": {
    "syllabus": [
      {
        "_id": "...",
        "number": "1.1",
        "title": "1.1 Characteristics of living organisms",
        "content": ["Describe the characteristics..."],
        "category": "General Biology",
        "level": "core",
        "keywords": ["characteristics", "living", "organisms"]
      }
    ],
    "pagination": {...}
  }
}
```

### GET /api/syllabus/:number

Get specific syllabus topic with related topics and question count.

**Response:**

```json
{
  "success": true,
  "data": {
    "syllabus": {...},
    "related_topics": [...],
    "question_count": 5
  }
}
```

### GET /api/syllabus/:number/questions

Get questions for a specific syllabus topic.

**Query Parameters:**

- Standard question filtering parameters

### GET /api/syllabus/categories/list

Get all available categories.

**Response:**

```json
{
  "success": true,
  "data": {
    "categories": [
      "Cell Biology",
      "Biochemistry",
      "Transport",
      "Genetics & Reproduction",
      "Ecology",
      "Coordination & Control",
      "Disease & Immunity",
      "General Biology"
    ]
  }
}
```

### GET /api/syllabus/tree

Get syllabus as hierarchical tree structure.

**Response:**

```json
{
  "success": true,
  "data": {
    "tree": [
      {
        "number": "1",
        "title": "Characteristics of living organisms",
        "subtopics": [
          {
            "number": "1.1",
            "title": "1.1 Characteristics of living organisms",
            "items": [...]
          }
        ],
        "items": [...]
      }
    ],
    "total_topics": 25
  }
}
```

### GET /api/syllabus/stats

Get syllabus statistics.

## Data Models

### Question Model

```javascript
{
  number: Number,              // Question number
  text: String,                // Question text
  subquestions: [SubQuestion], // Nested subquestions
  marks: Number,               // Total marks
  answer: String,              // Correct answer
  image: String|Array,         // Image path(s)
  ms_image: String,            // Mark scheme image
  syllabus: Syllabus,          // Main syllabus topic
  options: [String],           // MCQ options (A, B, C, D)
  paper: String,               // Paper code
  paper_type: String,          // mcq, sq, atp, as, a2
  subject: String,             // biology
  curriculum: String,          // igcse
  subject_code: String,        // 0610
  session: String,             // s20, w20, m20
  year: String,                // 2020, 2021
  variant: String,             // 22, 32
  topics: [String],            // Topic tags
  difficulty: String,          // easy, medium, hard
  keywords: [String],          // Search keywords
  createdAt: Date,
  updatedAt: Date
}
```

### Syllabus Model

```javascript
{
  number: String,              // Topic number (1.1, 2.1, etc.)
  title: String,               // Topic title
  content: [String],           // Content array
  subject: String,             // biology
  curriculum: String,          // igcse
  subject_code: String,        // 0610
  level: String,               // core, supplement, both
  category: String,            // Cell Biology, etc.
  description: String,         // Optional description
  prerequisites: [String],     // Required prior topics
  keywords: [String],          // Search keywords
  createdAt: Date,
  updatedAt: Date
}
```

## Usage Examples

### Frontend Integration

```javascript
// Get MCQ questions for photosynthesis
const response = await fetch(
  "/api/questions?paper_type=mcq&search=photosynthesis&limit=10"
);
const data = await response.json();

// Get questions by syllabus topic
const syllabusQuestions = await fetch("/api/syllabus/6.1/questions?year=2020");

// Get random practice questions
const randomQuestions = await fetch(
  "/api/questions/random?count=5&difficulty=medium"
);

// Search across all questions
const searchResults = await fetch("/api/questions?search=enzyme&page=1");
```

### Advanced Filtering

```javascript
// Multiple filters
const filteredQuestions = await fetch(
  "/api/questions?" +
    new URLSearchParams({
      paper_type: "mcq",
      year: "2020",
      session: "s20",
      syllabus: "6.1",
      difficulty: "medium",
      sort: "number",
      order: "asc",
    })
);

// Multiple values for same parameter
const multipleYears = await fetch(
  "/api/questions?year=2020&year=2021&paper_type=sq"
);
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "status": 400,
    "details": "Additional error details"
  }
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

### Rate Limiting

The API implements rate limiting:

- 100 requests per 15 minutes per IP address
- Exceeded requests return 429 status code

## Features

- **Comprehensive Filtering**: Filter by paper type, year, session, variant, syllabus topic, difficulty
- **Text Search**: Full-text search across question content
- **Pagination**: Efficient pagination with metadata
- **Statistics**: Question and syllabus statistics
- **Random Questions**: Generate practice sets
- **Hierarchical Syllabus**: Tree structure for topic browsing
- **Bulk Import**: Admin endpoints for data import
- **Error Handling**: Consistent error responses
- **Rate Limiting**: API protection against abuse
- **CORS**: Cross-origin request support
- **Security**: Helmet middleware for security headers

## Database Indexes

The API uses MongoDB indexes for optimal query performance:

- Text search indexes on question and syllabus content
- Compound indexes on frequently filtered fields
- Single field indexes on common query parameters

This ensures fast response times even with large datasets.
