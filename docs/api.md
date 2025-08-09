# API Documentation

## Daily Poll Quota

### `GET /daily/quota`
Returns the number of poll questions the authenticated user has answered today and when the quota resets.

Response
```json
{
  "answered": 0,
  "required": 3,
  "reset_at": "2024-01-02T00:00:00Z"
}
```

### `POST /daily/answer`
Submit an answer for a poll question. The request body should include the poll `question_id` and an optional `answer` object. The endpoint returns the updated quota payload described above.

Request
```json
{
  "question_id": "poll-1",
  "answer": {"choice": 2}
}
```
