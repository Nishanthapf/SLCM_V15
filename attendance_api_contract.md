# RFID Attendance API Contract

**Status**: Draft (To be implemented in Phase 2)
**Endpoint**: `/api/attendance/rfid/log`
**Method**: `POST`

## Description
This endpoint allows hardware devices (RFID Readers) to push swipe logs directly into the system. The system receives the data, validates basic structure, and stores it in the `Attendance Log` table for later background processing.

## Authentication
- **Type**: Bearer Token / API Key
- **Header**: `Authorization: token <api_key>:<api_secret>`
- **User**: Dedicated `RFID API User` (System User)

## Payload Schema
```json
{
    "rfid_uid": "String (Required) - Hexadecimal UID of the card",
    "device_id": "String (Required) - Unique ID of the reader",
    "timestamp": "Datetime (Required) - ISO 8601 Format (YYYY-MM-DD HH:mm:ss)"
}
```

## Success Response
**Code**: `200 OK`
```json
{
    "message": "Log received",
    "log_id": "LOG-2026-00012"
}
```

## Error Use Cases

### 1. Invalid Payload
**Code**: `400 Bad Request`
```json
{
    "error": "Missing required field: rfid_uid"
}
```

### 2. Device Not Registered
**Code**: `403 Forbidden`
```json
{
    "error": "Device ID not recognized"
}
```

## Implementation Notes
1. **Raw Storage**: Data is stored AS-IS in `Attendance Log` with `processed=0`.
2. **No Synchronous Calculation**: The API does NOT calculate attendance. It only accepts data.
3. **High Throughput**: logic must be minimal to handle burst traffic from multiple readers.
