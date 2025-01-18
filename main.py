import subprocess
import time
from typing import Optional

def get_latest_log(prover_id: str) -> Optional[str]:
    """获取最新的一行日志"""
    try:
        cmd = f"docker exec {prover_id} tail -n 1 /app/runtime.log"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"获取日志失败: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"执行命令出错: {str(e)}")
        return None

def check_sync_status(prover_id: str) -> bool:
    """检查是否处于同步状态"""
    sync_count = 0
    for _ in range(3):
        log = get_latest_log(prover_id)
        if log is None:
            return False
        
        if 'sync' in log.lower():
            sync_count += 1
        else:
            return False
            
        time.sleep(60)  # 等待1分钟
    
    return sync_count == 3

# 预定义的 prover_id 列表
PROVER_IDS = [ 1111
    # TODO: 添加预定义的 prover_id 列表
]

current_index = 0

def get_current_prover_id() -> str:
    """从预定义列表中获取当前的 prover_id"""
    global current_index
    if not PROVER_IDS:
        print("错误: PROVER_IDS 列表为空")
        exit(1)
    return PROVER_IDS[current_index]

def get_latest_prover_id() -> str:
    """从网站获取最新的 prover_id"""
    try:
        # TODO: 实现从网站获取最新 prover_id 的逻辑
        pass
    except Exception as e:
        print(f"获取最新 prover_id 失败: {str(e)}")
        exit(1)

def clear_docker_log(prover_id: str):
    """清空 Docker 的日志文件"""
    try:
        cmd = f"docker exec {prover_id} truncate -s 0 /app/runtime.log"
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"清空日志失败: {str(e)}")
        exit(1)

def switch_docker(new_prover_id: str):
    """切换到新的 Docker 容器"""
    global current_index
    try:
        # 停止当前容器
        current_id = get_current_prover_id()
        subprocess.run(f"docker stop {current_id}", shell=True, check=True)
        # 清空上一个容器的日志
        clear_docker_log(current_id)
        # 更新索引到下一个
        current_index = (current_index + 1) % len(PROVER_IDS)
        # 启动新容器
        subprocess.run(f"docker start {new_prover_id}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Docker 操作失败: {str(e)}")
        exit(1)

def is_docker_crashed(prover_id: str) -> bool:
    """检查 Docker 是否崩溃"""
    log = get_latest_log(prover_id)
    if log is None:
        return False
    return 'gs     0x0' in log

def restart_docker(prover_id: str):
    """重启崩溃的 Docker"""
    try:
        print(f"检测到 Docker {prover_id} 崩溃，正在重启...")
        subprocess.run(f"docker restart {prover_id}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"重启 Docker 失败: {str(e)}")
        exit(1)

def main():
    while True:
        try:
            current_id = get_current_prover_id()
            latest_id = get_latest_prover_id()
            
            # 检查当前 Docker 是否崩溃
            if is_docker_crashed(current_id):
                restart_docker(current_id)
                time.sleep(60)  # 等待重启完成
                continue
            
            # 如果最新的 id 小于当前 id，且当前 Docker 处于同步状态
            if latest_id < current_id and check_sync_status(current_id):
                switch_docker(latest_id)
            
            time.sleep(60)  # 每分钟检查一次
            
        except Exception as e:
            print(f"发生错误: {str(e)}")
            exit(1)

if __name__ == "__main__":
    main()
