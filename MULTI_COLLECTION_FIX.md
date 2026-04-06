# 多采集任务用户匹配修复

## 问题描述

当同一个用户（身份证号相同）存在于多个采集任务中时，系统会出现以下问题：

- 用户在采集任务A中的ID是10
- 用户在采集任务B中的ID是21
- 加载图像时，只查询身份证号，返回第一个结果（ID: 10）
- 如果选择采集任务B，就会提示"用户不属于该采集任务"

## 根本原因

User模型中有`collection_id`字段，表示用户属于某个采集任务。同一个身份证号可以在多个采集任务中存在，但每个采集任务中的用户ID不同。

```python
class User(Base):
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))  # 关键字段
    id_number = Column(String(18))  # 身份证号
    name = Column(String(50))
```

## 修复方案

### 修改前的查询逻辑
```python
# 只按身份证号查询，返回第一个结果
user = db.get_user_by_id_number(potential_id)
# 然后再检查用户是否在采集任务中
```

### 修改后的查询逻辑
```python
# 按身份证号 + 采集任务一起查询
user = db.get_user_by_id_number(potential_id, collection_id=self.current_collection_id)
# 直接返回该采集任务中的用户
```

## 代码改动

在`load_image()`方法中：

```python
# 按照身份证号和采集任务一起查询
user = db.get_user_by_id_number(potential_id, collection_id=self.current_collection_id)

if user:
    # 用户已经通过采集任务过滤，所以一定属于该采集任务
    self.current_user_id = user.id
    print(f"[INFO] 用户识别成功: {user.name}")
else:
    # 用户在该采集任务中不存在
    QMessageBox.warning(
        self,
        "警告",
        f"身份证号 {potential_id} 在选定的采集任务中不存在"
    )
    return
```

## 优势

1. **准确性**：直接查询到该采集任务中的用户，避免返回其他采集任务中的同名用户
2. **效率**：减少了后续的验证步骤，直接返回正确的用户
3. **简洁性**：代码逻辑更清晰，不需要再检查用户是否在采集任务中

## 使用场景

### 场景1：用户只在一个采集任务中
```
采集任务A: 李四 (ID: 10)
加载图像 → 查询 (身份证号, 采集任务A) → 找到用户 ✓
```

### 场景2：用户在多个采集任务中
```
采集任务A: 李四 (ID: 10)
采集任务B: 李四 (ID: 21)

选择采集任务A，加载图像 → 查询 (身份证号, 采集任务A) → 找到用户 (ID: 10) ✓
选择采集任务B，加载图像 → 查询 (身份证号, 采集任务B) → 找到用户 (ID: 21) ✓
```

### 场景3：用户不在选定的采集任务中
```
采集任务A: 李四 (ID: 10)
采集任务B: 王五 (ID: 20)

选择采集任务B，加载李四的图像 → 查询 (身份证号, 采集任务B) → 找不到 ✗
提示：身份证号在选定的采集任务中不存在
```

## 控制台输出示例

### 成功情况
```
[DEBUG] 查询身份证号: 110101199001010023
[DEBUG] 采集任务ID: 5
[DEBUG] 用户找到: 李四 (ID: 21, 采集任务ID: 5)
[INFO] 用户识别成功: 李四 (身份证: 110101199001010023, 采集任务: 5)
```

### 失败情况
```
[DEBUG] 查询身份证号: 110101199001010023
[DEBUG] 采集任务ID: 6
[WARNING] 身份证号 110101199001010023 在采集任务 6 中不存在
```

## 数据库查询对比

### 修改前
```sql
SELECT * FROM users WHERE id_number = '110101199001010023'
-- 返回第一个结果，可能来自任何采集任务
```

### 修改后
```sql
SELECT * FROM users 
WHERE id_number = '110101199001010023' 
AND collection_id = 5
-- 返回该采集任务中的用户
```

## 总结

这个修复确保了：
1. 用户查询时考虑采集任务的上下文
2. 同一身份证号在不同采集任务中的用户能被正确区分
3. 错误提示更准确，用户知道问题所在
