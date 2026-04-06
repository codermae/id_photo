# Camera View Fixes - 摄像头视图修复

## Issue 1: Photo Saving Error - "必须指定采集任务id"
**Status**: ✅ FIXED

### Root Cause
When saving a photo in camera view, the `SavePhotoThread.run()` method was not passing `collection_id` to `db.add_record()`. The database requires `collection_id` to create a new collection record.

### Solution
1. Modified `IDCardView.user_selected` signal to include `collection_id` parameter
   - Changed from: `pyqtSignal(int, str, object)` 
   - Changed to: `pyqtSignal(int, str, object, int)`

2. Updated all `user_selected.emit()` calls in `id_card_view.py` to pass `collection_id`

3. Modified `CameraView.set_current_user()` to accept and store `collection_id`
   - Added `self.current_collection_id = None` instance variable
   - Updated method signature to accept `collection_id` parameter

4. Modified `SavePhotoThread` class:
   - Added `collection_id` parameter to `__init__`
   - Passed `collection_id` to `db.add_record()` call in `run()` method

5. Updated `CameraView.take_photo()` to pass `collection_id` when creating `SavePhotoThread`

### Files Modified
- `id_photo_system/views/id_card_view.py`
- `id_photo_system/views/camera_view.py`

### Testing
- When user reads ID card and selects collection task, the collection_id is now passed through the signal chain
- When taking photo, the collection_id is passed to SavePhotoThread
- Photo saving should now work without "必须指定采集任务id" error

---

## Issue 2: Identity Verification Failure Message Clarity
**Status**: ✅ FIXED

### Root Cause
The identity verification failure message was showing "✗ 身份核验失败" with similarity percentage, but wasn't clear about:
- What the threshold is (60%)
- Why it failed
- What the user should do to fix it

### Solution
Improved the failure message to include:
1. Current similarity percentage
2. Required threshold (60%)
3. Clear explanation of why it failed
4. Actionable suggestions for the user

### New Message Format
```
✗ 身份核验失败

用户: [用户名]
相似度: [X.XX%]
所需阈值: 60%

原因: 采集照片与身份证照片相似度不足
请确保光线充足、面部清晰、表情自然
```

### Files Modified
- `id_photo_system/views/camera_view.py` (verify_identity method)

### Testing
- When identity verification fails, user now sees clear threshold and actionable suggestions
- Message is more helpful for troubleshooting

---

## Summary of Changes

### Signal Chain Update
```
IDCardView (reads ID card)
  ↓ emits user_selected(user_id, user_name, id_photo, collection_id)
  ↓
CameraView.set_current_user(user_id, user_name, id_photo, collection_id)
  ↓ stores collection_id
  ↓
CameraView.take_photo()
  ↓ passes collection_id to SavePhotoThread
  ↓
SavePhotoThread.run()
  ↓ passes collection_id to db.add_record()
  ↓
Database creates record with correct collection_id
```

### Key Variables Added
- `CameraView.current_collection_id`: Stores the collection task ID
- `SavePhotoThread.collection_id`: Receives and uses collection_id

### Backward Compatibility
- All changes are backward compatible
- If collection_id is None, database will raise appropriate error (as before)
- Signal connection in main_window.py automatically handles new parameter
