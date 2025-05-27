# Upload Flag Feature

This document describes the implementation of the `uploadFlag` feature for user management.

## Overview

The `uploadFlag` is a boolean field added to the user model that controls whether a user has permission to upload videos. This feature allows administrators to manage upload permissions on a per-user basis.

## Implementation Details

### Database Schema Changes

- **Column Name**: `uploadFlag`
- **Type**: Boolean
- **Default Value**: `false`
- **Nullable**: `false`

### Files Modified

1. **`app/models.py`**
   - Added `uploadFlag = Column(Boolean, default=False, nullable=False)` to the User model

2. **`app/schemas.py`**
   - Added `uploadFlag: bool` to `UserResponse` schema
   - Added `uploadFlag: Optional[bool] = None` to `UserUpdate` schema
   - Added `uploadFlag: Optional[bool] = None` to `UserProfile` schema

3. **`app/crud.py`**
   - Updated `update_user_profile()` function to handle `uploadFlag` updates
   - The `update_user()` function automatically handles `uploadFlag` via the existing `setattr` logic

### Migration Script

A migration script `add_upload_flag_migration.py` has been created to add the `uploadFlag` column to existing databases.

#### Running the Migration

```bash
# Run the migration script
python add_upload_flag_migration.py
```

The script will:
- Check if the `uploadFlag` column already exists
- Add the column with appropriate SQL for different database dialects (PostgreSQL, SQLite, etc.)
- Verify the migration was successful

## API Response Changes

### Before
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "bio": "Hello world",
  "profile_picture": "https://example.com/pic.jpg"
}
```

### After
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "uploadFlag": false,
  "created_at": "2023-01-01T00:00:00Z",
  "bio": "Hello world",
  "profile_picture": "https://example.com/pic.jpg"
}
```

## Affected Endpoints

The `uploadFlag` field is now included in responses from the following endpoints:

- `GET /api/users/me` - Get current user profile
- `GET /api/users/` - Get all users
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user (can also update uploadFlag)
- `PUT /api/users/profile` - Update user profile (can also update uploadFlag)

## Usage Examples

### Checking Upload Permission

```python
# In your video upload endpoint
@router.post("/videos/")
def upload_video(
    current_user = Depends(get_current_user),
    # ... other parameters
):
    if not current_user.uploadFlag:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to upload videos"
        )
    # ... proceed with upload
```

### Updating Upload Permission (Admin)

```python
# Update a user's upload permission
user_update = UserUpdate(uploadFlag=True)
updated_user = update_user(db, user_id="user-uuid", user_update=user_update)
```

## Testing

A test script `test_upload_flag.py` has been created to verify the implementation:

```bash
# Run the test script
python test_upload_flag.py
```

The test script verifies:
- The `uploadFlag` attribute exists on User models
- The `uploadFlag` field is included in UserResponse serialization
- The `uploadFlag` can be updated successfully

## Default Behavior

- **New Users**: All new users will have `uploadFlag = false` by default
- **Existing Users**: After running the migration, all existing users will have `uploadFlag = false`
- **API Compatibility**: The addition is backward compatible - existing API clients will receive the new field without breaking

## Security Considerations

- The `uploadFlag` should only be modifiable by administrators
- Consider implementing role-based access control for updating upload permissions
- The flag should be checked on all video upload endpoints

## Future Enhancements

Potential future improvements:
- Add audit logging for uploadFlag changes
- Implement role-based permissions (admin, moderator, user)
- Add bulk operations for managing upload permissions
- Add upload quota limits in addition to the boolean flag 