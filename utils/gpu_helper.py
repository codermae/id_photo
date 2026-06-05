"""
GPU辅助工具
用于检测GPU可用性、显示GPU信息、管理GPU内存
"""
import sys
import os

class GPUHelper:
    """GPU辅助类"""
    
    def __init__(self):
        self.torch_available = False
        self.cuda_available = False
        self.gpu_count = 0
        self.gpu_info = []
        
        self._detect_gpu()
    
    def _detect_gpu(self):
        """检测GPU可用性"""
        try:
            import torch
            self.torch_available = True
            self.cuda_available = torch.cuda.is_available()
            
            if self.cuda_available:
                self.gpu_count = torch.cuda.device_count()
                
                # 获取每个GPU的信息
                for i in range(self.gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # GB
                    
                    self.gpu_info.append({
                        'id': i,
                        'name': gpu_name,
                        'memory_gb': gpu_memory,
                        'cuda_capability': torch.cuda.get_device_capability(i)
                    })
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARNING] GPU检测失败: {e}")
    
    def is_available(self) -> bool:
        """GPU是否可用"""
        return self.cuda_available
    
    def get_device_count(self) -> int:
        """获取GPU数量"""
        return self.gpu_count
    
    def get_gpu_info(self, device_id: int = 0) -> dict:
        """获取指定GPU的信息"""
        if device_id < len(self.gpu_info):
            return self.gpu_info[device_id]
        return {}
    
    def get_all_gpu_info(self) -> list:
        """获取所有GPU的信息"""
        return self.gpu_info
    
    def get_memory_info(self, device_id: int = 0) -> dict:
        """获取GPU内存信息"""
        if not self.cuda_available:
            return {'error': 'CUDA不可用'}
        
        try:
            import torch
            torch.cuda.set_device(device_id)
            
            total_memory = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
            allocated_memory = torch.cuda.memory_allocated(device_id) / (1024**3)
            reserved_memory = torch.cuda.memory_reserved(device_id) / (1024**3)
            free_memory = total_memory - reserved_memory
            
            return {
                'device_id': device_id,
                'total_gb': round(total_memory, 2),
                'allocated_gb': round(allocated_memory, 2),
                'reserved_gb': round(reserved_memory, 2),
                'free_gb': round(free_memory, 2),
                'usage_percent': round((reserved_memory / total_memory) * 100, 1)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def clear_cache(self, device_id: int = 0):
        """清理GPU缓存"""
        if not self.cuda_available:
            return
        
        try:
            import torch
            torch.cuda.set_device(device_id)
            torch.cuda.empty_cache()
            print(f"[INFO] GPU {device_id} 缓存已清理")
        except Exception as e:
            print(f"[WARNING] 清理GPU缓存失败: {e}")
    
    def print_status(self):
        """打印GPU状态"""
        print("\n" + "="*60)
        print("GPU状态检测")
        print("="*60)
        
        if not self.torch_available:
            print("❌ PyTorch未安装")
            print("\n安装方法:")
            print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
            return
        
        if not self.cuda_available:
            print("❌ CUDA不可用")
            print("\n可能的原因:")
            print("  1. 没有NVIDIA显卡")
            print("  2. CUDA未安装或版本不匹配")
            print("  3. PyTorch是CPU版本")
            print("\n解决方法:")
            print("  1. 安装CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
            print("  2. 安装GPU版PyTorch:")
            print("     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
            return
        
        print(f"✅ CUDA可用")
        print(f"✅ 检测到 {self.gpu_count} 个GPU\n")
        
        for info in self.gpu_info:
            print(f"GPU {info['id']}: {info['name']}")
            print(f"  显存: {info['memory_gb']:.2f} GB")
            print(f"  CUDA能力: {info['cuda_capability']}")
            
            # 获取内存使用情况
            mem_info = self.get_memory_info(info['id'])
            if 'error' not in mem_info:
                print(f"  已用显存: {mem_info['allocated_gb']:.2f} GB / {mem_info['total_gb']:.2f} GB ({mem_info['usage_percent']:.1f}%)")
                print(f"  可用显存: {mem_info['free_gb']:.2f} GB")
            print()
        
        print("="*60 + "\n")
    
    def get_recommended_config(self) -> dict:
        """获取推荐的GPU配置"""
        if not self.cuda_available:
            return {
                'USE_GPU': False,
                'GPU_DEVICE_ID': 0,
                'reason': 'CUDA不可用'
            }
        
        # 选择显存最大的GPU
        best_gpu = max(self.gpu_info, key=lambda x: x['memory_gb'])
        
        return {
            'USE_GPU': True,
            'GPU_DEVICE_ID': best_gpu['id'],
            'GPU_NAME': best_gpu['name'],
            'GPU_MEMORY_GB': best_gpu['memory_gb'],
            'reason': f"选择显存最大的GPU ({best_gpu['memory_gb']:.2f} GB)"
        }


def check_gpu_status():
    """检查GPU状态（命令行工具）"""
    helper = GPUHelper()
    helper.print_status()
    
    # 打印推荐配置
    config = helper.get_recommended_config()
    print("推荐配置:")
    print(f"  USE_GPU = {config['USE_GPU']}")
    if config['USE_GPU']:
        print(f"  GPU_DEVICE_ID = {config['GPU_DEVICE_ID']}")
        print(f"  原因: {config['reason']}")
    else:
        print(f"  原因: {config['reason']}")
    print()


if __name__ == '__main__':
    check_gpu_status()
