from markupsafe import escape


def render_strategy_review_email(strategy_name, status, reason=None):
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
        f"<p>策略名称：{escape(strategy_name)}</p>"
        f"<p>审核结果：{escape(status_label)}</p>"
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


def render_data_source_alert_email(source_name, checked_at, error_message):
    subject = f"[QYQuant] 数据源异常：{source_name} 不可用"
    body_html = (
        "<html><body>"
        "<p>您好，</p>"
        f"<p>监控发现数据源 <strong>{escape(source_name)}</strong> 当前不可用。</p>"
        f"<p>最近检查时间：{escape(checked_at)}</p>"
        f"<p>错误信息：{escape(error_message or '未知错误')}</p>"
        "<p>请尽快检查数据源账号、网络连通性和上游服务状态。</p>"
        "</body></html>"
    )
    body_text = (
        "您好，\n"
        f"监控发现数据源 {source_name} 当前不可用。\n"
        f"最近检查时间：{checked_at}\n"
        f"错误信息：{error_message or '未知错误'}\n"
        "请尽快检查数据源账号、网络连通性和上游服务状态。"
    )
    return subject, body_html, body_text


def render_data_source_recovered_email(source_name, checked_at):
    subject = f"[QYQuant] 数据源恢复：{source_name} 已恢复"
    body_html = (
        "<html><body>"
        "<p>您好，</p>"
        f"<p>监控发现数据源 <strong>{escape(source_name)}</strong> 已恢复正常。</p>"
        f"<p>最近检查时间：{escape(checked_at)}</p>"
        "<p>当前无需人工干预，可继续关注后续健康检查结果。</p>"
        "</body></html>"
    )
    body_text = (
        "您好，\n"
        f"监控发现数据源 {source_name} 已恢复正常。\n"
        f"最近检查时间：{checked_at}\n"
        "当前无需人工干预，可继续关注后续健康检查结果。"
    )
    return subject, body_html, body_text
