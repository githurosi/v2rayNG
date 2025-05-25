import os
import re
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List

# 路径配置（适配GitHub Actions环境）
LOG_PATH = os.path.join(os.path.dirname(__file__), "../commits.log")
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "../logs/v2rayng_commits.json")
README_PATH = os.path.join(os.path.dirname(__file__), "../README.md")  # 修复变量名拼写

@dataclass
class Commit:
    hash: str
    author: str
    date: str
    message: str

def parse_logs() -> List[Commit]:
    """解析Git提交日志文件"""
    commits = []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    try:
                        # 标准化日期格式：Mon Mar 15 09:30:45 2024 +0800 → ISO8601
                        dt = datetime.strptime(
                            parts[2], "%a %b %d %H:%M:%S %Y %z"
                        )
                        iso_date = dt.isoformat()
                    except ValueError:
                        iso_date = parts[2]  # 保留原始日期格式

                    commits.append(Commit(
                        hash=parts[0][:7],       # 取短哈希
                        author=parts[1].strip(),
                        date=iso_date,
                        message=parts[3][:50].replace("|", "丨")  # 防止表格格式破坏
                    ))
        return commits
    except FileNotFoundError:
        print(f"错误：日志文件 {LOG_PATH} 不存在")
        return []
    except Exception as e:
        print(f"解析日志时发生错误: {str(e)}")
        return []

def generate_report(commits: List[Commit]) -> dict:
    """生成统计报告"""
    if not commits:
        return {}

    authors = {c.author for c in commits}
    dates = [datetime.fromisoformat(c.date) for c in commits if c.date]
    
    return {
        "total_commits": len(commits),
        "active_authors": len(authors),
        "first_commit": min(dates).isoformat() if dates else "",
        "last_commit": max(dates).isoformat() if dates else "",
        "top_authors": sorted(
            [(a, sum(1 for c in commits if c.author == a)) 
             for a in authors],
            key=lambda x: x[1],
            reverse=True
        )[:3]  # 取提交量前三的作者
    }

def update_readme(report: dict):
    """更新README的统计信息"""
    if not report:
        return

    try:
        # 修复文件操作语法和模式
        with open(README_PATH, "r+", encoding="utf-8") as f:
            content = f.read()
            
            # 使用更稳健的正则匹配
            marker = "### v2rayNG 提交统计"
            stats_block = (
                f"{marker}\n\n"
                f"- 总提交数: **{report['total_commits']}**\n"
                f"- 最近更新: `{report['last_commit'][:10]}`\n"
                f"- 活跃开发者: **{report['active_authors']}**\n"
                f"- 核心贡献者（Top 3）:\n"
            )
            
            # 添加贡献者列表
            for author, count in report.get("top_authors", []):
                stats_block += f"  - `{author}` ({count}次提交)\n"
            
            # 动态更新或新建区块
            if marker in content:
                new_content = re.sub(
                    rf"({re.escape(marker)}).*?(?=\n### |$)",
                    stats_block,
                    content,
                    flags=re.DOTALL
                )
            else:
                new_content = content + "\n\n" + stats_block
            
            # 回写文件
            f.seek(0)
            f.write(new_content)
            f.truncate()
            print("README.md 更新成功")
            
    except FileNotFoundError:
        print(f"错误：README文件 {README_PATH} 不存在")
    except PermissionError:
        print(f"错误：无权限修改 {README_PATH}")
    except Exception as e:
        print(f"更新README时发生错误: {str(e)}")

def main():
    # 解析日志
    commits = parse_logs()
    if not commits:
        return
    
    # 生成报告
    report = generate_report(commits)
    
    # 保存结构化数据
    try:
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": report,
                "recent_commits": [c.__dict__ for c in commits[-10:]]  # 最近10条
            }, f, indent=2, ensure_ascii=False)
        print(f"日志数据已保存至 {OUTPUT_JSON}")
    except Exception as e:
        print(f"保存JSON时出错: {str(e)}")
    
    # 更新README
    update_readme(report)

if __name__ == "__main__":
    main()
