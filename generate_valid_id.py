"""
生成有效的身份证号码（用于测试）
"""
from utils.id_card_validator import IDCardValidator

def generate_valid_id_card(area_code='110101', birth_date='19900101', sequence='001'):
    """
    生成有效的18位身份证号
    
    Args:
        area_code: 地区码（6位）
        birth_date: 出生日期（8位，YYYYMMDD）
        sequence: 顺序码（3位，最后一位奇数=男，偶数=女）
    
    Returns:
        str: 完整的18位身份证号（包含校验码）
    """
    # 前17位
    id_17 = area_code + birth_date + sequence
    
    if len(id_17) != 17:
        raise ValueError(f"前17位长度不正确: {len(id_17)}")
    
    # 计算校验码
    total = 0
    for i in range(17):
        total += int(id_17[i]) * IDCardValidator.WEIGHTS[i]
    
    remainder = total % 11
    check_code = IDCardValidator.CHECK_CODES[remainder]
    
    # 完整身份证号
    id_card = id_17 + check_code
    
    return id_card


if __name__ == '__main__':
    print("=" * 60)
    print("生成有效的测试身份证号")
    print("=" * 60)
    
    # 生成几个测试用的身份证号
    test_ids = [
        ('110101', '19900101', '001'),  # 北京，1990-01-01，男
        ('110101', '19900101', '002'),  # 北京，1990-01-01，女
        ('310101', '19850315', '123'),  # 上海，1985-03-15，男
        ('440101', '19920520', '456'),  # 广州，1992-05-20，女
        ('500101', '19880808', '789'),  # 重庆，1988-08-08，男
    ]
    
    print("\n生成的有效身份证号:\n")
    for area, birth, seq in test_ids:
        id_card = generate_valid_id_card(area, birth, seq)
        
        # 验证
        result = IDCardValidator.validate(id_card)
        status = '✅' if result['valid'] else '❌'
        
        info = result.get('info', {})
        gender = info.get('gender', '未知')
        birth_date = info.get('birth_date', '未知')
        
        print(f"{status} {id_card} - {birth_date}, {gender}")
    
    print("\n" + "=" * 60)
    print("这些身份证号可以用于测试系统")
    print("=" * 60)
