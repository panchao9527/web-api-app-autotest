"""
从 junit xml 汇总测试结果并推送通知（CI 用）
- 汇总所有 junit 报告的通过/失败数，合并成一条推送到钉钉/企微/邮件
- 用法: python scripts/notify_from_junit.py <junit结果目录>
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

# 把项目根目录加入 sys.path，保证能 import clients/config
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def collect(junit_dir: str):
    total = failed = skipped = 0
    duration = 0.0
    for path in glob.glob(os.path.join(junit_dir, "**", "*.xml"), recursive=True):
        try:
            root = ET.parse(path).getroot()
        except Exception:  # noqa
            continue
        for s in root.iter("testsuite"):
            total += int(s.get("tests", 0) or 0)
            failed += int(s.get("failures", 0) or 0) + int(s.get("errors", 0) or 0)
            skipped += int(s.get("skipped", 0) or 0)
            duration += float(s.get("time", 0) or 0)
    passed = total - failed - skipped
    return total, passed, failed, duration


def main():
    junit_dir = sys.argv[1] if len(sys.argv) > 1 else "junit"
    total, passed, failed, duration = collect(junit_dir)
    dur = f"{duration:.1f}s"
    report_url = os.getenv("REPORT_URL", "")
    print(f"汇总结果 | 总计{total} 通过{passed} 失败{failed} 耗时{dur}")

    if total == 0:
        print("未找到 junit 结果，跳过通知")
        return

    # 钉钉/企微
    try:
        from clients.notify import Notifier
        Notifier().send_test_result(total=total, passed=passed, failed=failed,
                                    duration=dur, report_url=report_url)
    except Exception as e:  # noqa
        print(f"钉钉/企微通知失败: {e}")

    # 邮件(配了才发)
    try:
        from config.settings import settings
        if settings.email.get("host") and settings.email.get("to"):
            from clients.email_client import EmailSender
            EmailSender().send_report(total=total, passed=passed, failed=failed,
                                      duration=dur, report_url=report_url)
    except Exception as e:  # noqa
        print(f"邮件通知失败: {e}")


if __name__ == "__main__":
    main()
