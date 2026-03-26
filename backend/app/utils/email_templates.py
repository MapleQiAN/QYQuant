def render_strategy_review_email(strategy_name, status, reason=None):
    from markupsafe import escape

    status_map = {
        "approved": "通过",
        "rejected": "拒绝",
    }
    status_label = status_map.get(status, status)
    subject = "[QYQuant] 您的策略审核结果通知"
    reason_html = f"<p><strong>拒绝原因：</strong>{escape(reason)}</p>" if reason else ""
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


def render_strategy_takedown_email(strategy_name, reason):
    from markupsafe import escape

    subject = "[QYQuant] 您的策略已被下架"
    body_html = (
        "<html><body>"
        "<p>您好，</p>"
        f"<p>您的策略《{escape(strategy_name)}》已被平台下架。</p>"
        f"<p><strong>下架原因：</strong>{escape(reason)}</p>"
        "<p>如您认为该处理有误，请联系平台支持并补充相关说明材料。</p>"
        "</body></html>"
    )
    body_text = (
        "您好，\n"
        f"您的策略《{strategy_name}》已被平台下架。\n"
        f"下架原因：{reason}\n"
        "如您认为该处理有误，请联系平台支持并补充相关说明材料。"
    )
    return subject, body_html, body_text
