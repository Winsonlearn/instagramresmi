# API Documentation

This document describes the API endpoints available in the Instagram Clone application.

## Base URL

All API endpoints are relative to the application base URL (default: `http://127.0.0.1:5000`).

## Authentication

Most endpoints require authentication. Authentication is handled via Flask-Login sessions.

## Endpoints

### Authentication Endpoints

#### POST `/auth/login`

Log in a user.

**Request Body:**

- `username` (string, required): Username
- `password` (string, required): User password

**Response:**

- Success: Redirect to feed page
- Error: Flash message with error

#### POST `/auth/signup`

Register a new user.

**Request Body:**

- `username` (string, required): Username (3-30 characters)
- `email` (string, required): Email address
- `fullname` (string, required): Full name
- `password` (string, required): Password (min 6 characters)

**Response:**

- Success: Redirect to login page
- Error: Flash message with validation errors

#### GET `/auth/logout`

Log out current user.

**Response:** Redirect to index page

---

### Posts

#### GET `/posts/create`

Display post creation form.

**Authentication:** Required

#### POST `/posts/create`

Create a new post.

**Authentication:** Required

**Request Body (multipart/form-data):**

- `image` (file, required): Image file (max 16MB)
- `caption` (string, optional): Post caption

**Response:**

- Success: Redirect to feed with success message
- Error: Flash message with error

#### GET `/posts/<post_id>`

View a single post with comments.

**Authentication:** Required

**Parameters:**

- `post_id` (integer): Post ID

**Response:** Rendered template with post details

#### POST `/posts/<post_id>/like`

Toggle like on a post.

**Authentication:** Required

**Response (JSON):**

```json
{
  "liked": true,
  "like_count": 42
}
```

#### POST `/posts/<post_id>/bookmark`

Toggle bookmark on a post.

**Authentication:** Required

**Response (JSON):**

```json
{
  "bookmarked": true
}
```

#### POST `/posts/<post_id>/comment`

Add a comment to a post.

**Authentication:** Required

**Request Body:**

- `content` (string, required): Comment content (max 2200 characters)

**Response:** Redirect to post detail page

#### POST `/posts/<post_id>/edit`

Edit a post caption (only by owner).

**Authentication:** Required

**Request Body:**

- `caption` (string, optional): New caption

**Response:**

- Success: Redirect to post detail page
- Error: Flash message with error

#### POST `/posts/<post_id>/delete`

Delete a post (only by owner).

**Authentication:** Required

**Response:**

- Success: Redirect to feed with success message
- Error: Flash message with error

#### POST `/posts/comment/<comment_id>/edit`

Edit a comment (only by owner).

**Authentication:** Required

**Request Body:**

- `content` (string, required): New comment content

**Response:** Redirect to post detail page

#### POST `/posts/comment/<comment_id>/delete`

Delete a comment (only by owner).

**Authentication:** Required

**Response:** Redirect to post detail page

---

### Main Routes

#### GET `/`

Landing page. Redirects to feed if authenticated.

#### GET `/feed`

Personalized feed showing posts from followed users.

**Authentication:** Required

**Query Parameters:**

- `page` (integer, optional): Page number (default: 1)

**Response:** Rendered feed template with pagination

#### GET `/explore`

Explore page showing all posts.

**Authentication:** Required

**Query Parameters:**

- `page` (integer, optional): Page number (default: 1)

**Response:** Rendered explore template with pagination

**Caching:** Cached for 60 seconds

#### GET `/search`

Search for users and posts.

**Authentication:** Required

**Query Parameters:**

- `q` (string, required): Search query (min 2 characters)
- `type` (string, optional): Search type - `user` or `hashtag` (default: `user`)

**Response:** Rendered search template with results

#### GET `/saved`

View saved/bookmarked posts.

**Authentication:** Required

**Response:** Rendered saved template with bookmarked posts

---

### Profiles

#### GET `/profiles/<username>`

View user profile.

**Authentication:** Required

**Response:** Rendered profile template

#### GET `/profiles/<username>/follow`

Follow/unfollow a user.

**Authentication:** Required

**Response:** JSON with follow status

#### GET `/profiles/edit`

Edit own profile.

**Authentication:** Required

#### POST `/profiles/edit`

Update profile information.

**Authentication:** Required

**Request Body (multipart/form-data):**

- `profile_picture` (file, optional): New profile picture
- `fullname` (string, optional): Full name
- `bio` (string, optional): Bio text

**Response:** Redirect to profile page

#### GET `/profiles/settings`

View account settings.

**Authentication:** Required

#### POST `/profiles/settings`

Update account settings (password, etc.).

**Authentication:** Required

---

### Notifications

#### GET `/notifications`

View all notifications.

**Authentication:** Required

**Response:** Rendered notifications template

#### GET `/notifications/count`

Get unread notification count.

**Authentication:** Required

**Response (JSON):**

```json
{
  "count": 5
}
```

#### POST `/notifications/<notification_id>/read`

Mark notification as read.

**Authentication:** Required

**Response:** JSON with success status

---

## Error Responses

### 404 Not Found

Resource not found. Renders 404 error page.

### 500 Internal Server Error

Server error. Renders 500 error page.

### 413 Request Entity Too Large

File upload exceeds maximum size (16MB). Flash error message.

## Rate Limiting

Currently, rate limiting is not implemented but recommended for production. Consider using Flask-Limiter.

## Caching Strategy

- **Explore Page**: Cached for 60 seconds
- **Client-side API responses**: Cached for 5 minutes
- Cache is automatically cleared on data mutations (post creation, updates, etc.)

## Best Practices

1. Always handle errors gracefully
2. Use appropriate HTTP methods (GET for reads, POST for mutations)
3. Validate all input data
4. Use CSRF tokens for all forms
5. Implement proper authentication checks
6. Cache appropriately based on data freshness requirements
