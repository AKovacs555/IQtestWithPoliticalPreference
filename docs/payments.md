# Payments IPN

## NOWPayments callback

`POST /payments/nowpayments/ipn` receives payment notifications from
[NOWPayments](https://nowpayments.io). The request body must be the JSON payload
sent by NOWPayments and include the `x-nowpayments-sig` header. The signature is
an HMAC-SHA512 of the JSON body with keys sorted:

```
signature = hmac.new(IPN_SECRET, json.dumps(body, sort_keys=True), sha512)
```

If the signature is valid and the `payment_status` is `finished` or
`confirmed`, the user referenced by `order_id`/`user_id` receives one extra
free attempt.

### Responses

| status | body | description |
|--------|------|-------------|
| 200 | `{ "credited": true }` | payment verified and credited |
| 200 | `{ "credited": false }` | valid notification but not finished |
| 400 | `{ "code": "BAD_SIGNATURE" }` | signature mismatch |
| 409 | `{ "code": "ALREADY_PROCESSED" }` | duplicate `payment_id` |

All notifications are stored in the `payments` table for durability and
idempotency.
