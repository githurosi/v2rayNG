import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List

LOG_PATH = os.path.join(os.path.dirname(__file__), "../commits.log")
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "../logs/v2rayng_commits.json")
README_PATH = os.path.join(os.path.dirname(__file__), "../README.md")

@dataclass
class Commit:
    hash: str
    author: str
    date: str
    message: str

def parse_logs() -> List[Commit]:
    commits = []
    with open(LOG_PATH, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 4:
                # 标准化时间格式：2024-03-15 09:30:45 +0800 → ISO格式
                raw_date = parts[2]
                dt = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %Y %z")
                iso_date = dt.isoformat()
                
                commits.append(Commit(
                    hash=parts[0],
                    author=parts[1],
                    date=iso_date,
                    message=parts[3][:50]  # 截取前50字符
                ))
    return commits

def generate_report(commits: List[Commit]):
    # 生成统计信息
    authors = {c.author for c in commits}
    first_commit = min(commits, key=lambda x: x.date)
    last_commit = max(commits, key=lambda x: x.date)
    
    return {
        "total_commits": len(commits),
        "active_authors": len(authors),
        "first_commit": first_commit.date,
        "last_commit": last_commit.date,
        "authors": list(authors)
    }

def update_readme(report: dict):
    with open(README_PATH, "r+") as f:
        content = f.read()
        
        # 查找或创建v2rayNG统计区块
        marker = "### v2rayNG 提交统计"
        if marker not in content:
            content += f"\n\n{marker}\n"
            
        # 更新统计信息
        new_content = re.sub(
            rf"({marker}\n).*?(\n\n|$)",
            f"\\1\n"
            f"- 总提交数: {report['total_commits']}\n"
            f"- 最近提交: {report['last_commit'][:10]}\n"
            f"- 活跃开发者: {len(report['authors'])}\n"
            f"\\2",
            content,
            flags=re.DOTALL
        )
        
        f.seek(0)
        f.write(new_content)
        f.truncate()

def main():
    # 解析原始日志
    commits = parse_logs()
    
    # 生成结构化数据
    report = generate_report(commits)
    
    # 保存JSON日志
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump({
            "metadata": report,
            "commits": [c.__dict__ for c in commits[-50:]]  # 保留最近50条
        }, f, indent=2)
    
    # 更新README
    update_readme(report)

if __name__ == "__main__":
    main()
