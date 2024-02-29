import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

async def send_email(subject:str, message:str, attachment_paths:list):
    from_email = 'eric0000567@gmail.com'
    to_email = ['eric0000567@gmail.com']#, 'a0986676810@gmail.com']

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Gmail的SMTP端口号

    username = 'eric0000567@gmail.com'
    password = 'cgxi amcz vqdz onqi'

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_email)
    msg['Subject'] = subject

    # 添加邮件正文
    msg.attach(MIMEText(message, 'plain'))

    # 添加附件
    for attachment_path in attachment_paths:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read())
            part.add_header('Content-Disposition', f'attachment; filename={attachment_path}')
            msg.attach(part)
    # 连接到邮件服务器并发送邮件
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(from_email, to_email, msg.as_string())
        print("send email successful")
    except Exception as e:
        print(f"FAIL send email：{str(e)}")
    finally:
        server.quit()
                          