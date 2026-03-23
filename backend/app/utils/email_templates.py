def render_strategy_review_email(strategy_name, status, reason=None):
    status_map = {
        'approved': '通过',
        'rejected': '拒绝',
    }
    status_label = status_map.get(status, status)
    subject = "[QYQuant] 您的策略审核结果通知"
    reason_html = f"<p><strong>拒绝原因：</strong>{reason}</p>" if reason else ""
    reason_text = f"\n拒绝原因：{reason}" if reason else ""
    body_html = (
        "<html><body>"
        "<p>您好，</p>"
        f"<p>策略名称：{strategy_name}</p>"
        f"<p>审核结果：{status_label}</p>"
        f"{reason_html}"
        "<p>请登录 QYQuant 查看详情。</p>"
        "</body></html>"
    )
    body_text = (
        "您好，\n"
        f"策略名称：{strategy_name}\n"
        f"审核结果：{status_label}"
        f"{reason_text}\n"
        "请登录 QYQuant 查看详情。"
    )
    return subject, body_html, body_text
