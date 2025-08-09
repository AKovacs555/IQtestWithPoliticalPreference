# API Reference

## Daily quota

### `GET /daily/quota`

Returns current status of the Daily 3 poll quota for the authenticated user.

**Response**
```
{
  "answered": <int>,
  "required": 3,
  "reset_at": "<ISO8601 UTC timestamp>"
}
```

### `POST /daily/answer`

Submit a poll answer for the current day. The request body should include the
survey item identifier and the selected option index.

**Request body**
```
{
  "item_id": "<question id>",
  "answer_index": <int>
}
```

**Response** – same as `GET /daily/quota` after the answer is recorded.
