# Camera View Test Guide - 摄像头视图测试指南

## Test Case 1: Photo Saving with Collection Task
**Objective**: Verify that photos can be saved without "必须指定采集任务id" error

### Steps
1. Start the application
2. Go to "身份证读取" (ID Card Reading) tab
3. Select a collection task from the dropdown (e.g., "默认采集任务")
4. Read an ID card (or use test mode to simulate)
5. Go to "拍照采集" (Camera Capture) tab
6. Verify that user information is displayed:
   - Current User ID shows the user ID
   - User Name shows the user name
7. Open camera
8. Click "拍照" (Take Photo) button
9. **Expected Result**: Photo saves successfully with message "照片已保存"
10. **Verify**: Check that no error message "必须指定采集任务id" appears

### What Changed
- Collection task ID is now passed from ID card reader to camera view
- SavePhotoThread receives collection_id and passes it to database
- Database can now create collection record with correct collection_id

---

## Test Case 2: Identity Verification Failure Message
**Objective**: Verify that identity verification failure message is clear and helpful

### Steps
1. Go to "拍照采集" (Camera Capture) tab
2. Select a user (via ID card reader or manual selection)
3. Open camera
4. Click "身份核验" (Identity Verification) button
5. Position face so it doesn't match the ID card photo well (e.g., different angle, lighting)
6. **Expected Result**: See failure message with:
   - Current similarity percentage
   - Required threshold (60%)
   - Clear explanation: "采集照片与身份证照片相似度不足"
   - Actionable suggestion: "请确保光线充足、面部清晰、表情自然"

### What Changed
- Failure message now includes threshold value (60%)
- Message explains why verification failed
- Message provides actionable suggestions for user

---

## Test Case 3: Collection ID Propagation
**Objective**: Verify that collection_id is correctly passed through the signal chain

### Steps
1. Add debug output to verify collection_id is passed:
   - Check console output when reading ID card
   - Should see: "[INFO] 设置当前用户: ID=..., 名称=..., 有照片=..., 采集任务ID=..."
   - Should see: "[INFO] 启动保存照片线程..." with collection_id
   - Should see: "[INFO] 创建采集记录: record_id=..., status=completed, collection_id=..."

2. Verify database record is created with correct collection_id:
   - Query database: `SELECT * FROM collection_record WHERE user_id = ?`
   - Verify `collection_id` matches the selected collection task

### What Changed
- Signal now includes collection_id parameter
- CameraView stores collection_id
- SavePhotoThread receives and uses collection_id

---

## Test Case 4: Multiple Collection Tasks
**Objective**: Verify that system works correctly with multiple collection tasks

### Steps
1. Create multiple collection tasks in database
2. Go to "身份证读取" tab
3. Select first collection task
4. Read ID card for user A
5. Go to "拍照采集" tab
6. Take photo - should save to first collection task
7. Go back to "身份证读取" tab
8. Select second collection task
9. Read ID card for user B
10. Go to "拍照采集" tab
11. Take photo - should save to second collection task
12. Verify both photos are saved with correct collection_id

### What Changed
- Each collection task now correctly receives its own collection_id
- Photos are saved to correct collection task

---

## Debugging Tips

### If photo saving still fails with "必须指定采集任务id"
1. Check console output for: "[INFO] 创建采集记录: record_id=..., collection_id=..."
2. If collection_id is None, check:
   - Is collection task selected in ID card reader?
   - Is user_selected signal being emitted with collection_id?
   - Add debug print in SavePhotoThread.__init__ to verify collection_id is received

### If identity verification message is not clear
1. Check that similarity percentage is displayed correctly
2. Verify threshold is shown as "60%"
3. Check that actionable suggestions are visible

### Console Output to Look For
```
[INFO] 设置当前用户: ID=1, 名称=张三, 有照片=True, 采集任务ID=1
[INFO] 启动保存照片线程...
[INFO] 保存原始照片...
[INFO] 添加照片记录...
[INFO] 提取并保存人脸特征...
[INFO] 更新采集记录...
[INFO] 创建采集记录: record_id=1, status=completed, collection_id=1
[INFO] 照片保存成功
```

---

## Rollback Instructions
If issues occur, the changes can be rolled back:

1. Revert `id_card_view.py`:
   - Change signal back to: `user_selected = pyqtSignal(int, str, object)`
   - Remove collection_id from emit calls

2. Revert `camera_view.py`:
   - Remove `self.current_collection_id` variable
   - Remove collection_id parameter from `set_current_user()`
   - Remove collection_id parameter from `SavePhotoThread.__init__()`
   - Remove collection_id from `db.add_record()` call

3. No changes needed to `main_window.py` - it will still work with fewer parameters
