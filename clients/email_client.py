"""
邮件客户端（发送测试报告摘要）
- 基于标准库 smtplib，无需额外依赖
- SMTP 配置来自 .env（SMTP_HOST/PORT/USER/PASSWORD、EMAIL_TO）
- 默认走 SSL(465)；收件人可用逗号分隔多个
- 用法:
    from clients.email_client import EmailSender
    EmailSender().send_report(total=50, passed=48, failed=2, duration="3m", report_url="http://...")
"""
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import settings
from utils.logger import log


class EmailSender:
    def __init__(self, cfg: dict = None):
        c = cfg or settings.email
        self.host = c.get("host", "")
        self.port = int(c.get("port", 465) or 465)
        self.user = c.get("user", "")
        self.password = c.get("password", "")
        self.to = c.get("to", "")

    def send_report(self, total, passed, failed, duration="", report_url="",
                    subject="自动化测试报告"):
        """发送测试结果摘要邮件(HTML 表格)"""
        if not (self.host and self.to):
            log.warning("未配置 SMTP/收件人，跳过邮件通知")
            return
        pass_rate = f"{(passed / total * 100):.1f}%" if total else "N/A"
        color = "#52c41a" if failed == 0 else "#ff4d4f"
        report_line = (f'<p>报告：<a href="{report_url}">{report_url}</a></p>'
                       if report_url else "")
        html = f"""
        <h3>{subject}（环境：{settings.env}）</h3>
        <table border="1" cellspacing="0" cellpadding="8" style="border-collapse:collapse">
          <tr><td>总计</td><td>{total}</td></tr>
          <tr><td>通过</td><td>{passed}</td></tr>
          <tr><td>失败</td><td style="color:{color}"><b>{failed}</b></td></tr>
          <tr><td>通过率</td><td>{pass_rate}</td></tr>
          <tr><td>耗时</td><td>{duration or '-'}</td></tr>
        </table>
        {report_line}
        """
        self._send(subject, html)

    def _send(self, subject: str, html: str, attachment: str = None):
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = self.to
        msg.attach(MIMEText(html, "html", "utf-8"))
        if attachment:
            with open(attachment, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header("Content-Disposition", "attachment",
                                filename=attachment.split("/")[-1])
                msg.attach(part)
        try:
            recipients = [x.strip() for x in self.to.split(",") if x.strip()]
            with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as s:
                s.login(self.user, self.password)
                s.sendmail(self.user, recipients, msg.as_string())
            log.info(f"邮件已发送 -> {self.to}")
        except Exception as e:  # noqa
            log.error(f"邮件发送失败: {e}")
