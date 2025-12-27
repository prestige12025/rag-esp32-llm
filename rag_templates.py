"""
rag_templates.py
社内文書テンプレ自動挿入モジュール
"""

import re

# ==================================================
# 共通テンプレ部品
# ==================================================

DEFAULT_SUBJECT = "件名：＜内容を簡潔に要約した件名＞"

DEFAULT_CLOSING = (
    "ご確認のほど、よろしくお願いいたします。\n"
    "以上"
)

INQUIRY_CLOSING = (
    "上記につきまして、ご判断を賜りたく存じます。\n"
    "何卒よろしくお願いいたします。\n"
    "以上"
)

REPORT_CLOSING = (
    "以上、ご報告申し上げます。"
)

# ==================================================
# 文書タイプ別テンプレ定義
# ==================================================

DOC_TEMPLATES = {
    # 汎用（事務連絡・通知など）
    "default": {
        "subject": DEFAULT_SUBJECT,
        "closing": DEFAULT_CLOSING,
    },

    # 伺い
    "doc_inquiry": {
        "subject": "件名：＜〇〇の件につきまして（伺い）＞",
        "closing": INQUIRY_CLOSING,
    },

    # 報告
    "doc_report": {
        "subject": "件名：＜〇〇の件 ご報告＞",
        "closing": REPORT_CLOSING,
    },

    # 復命（あとで強化）
    "doc_return_report": {
        "subject": "件名：＜ご指示事項に関する復命の件＞",
        "closing": REPORT_CLOSING,
    },
}

# ==================================================
# 判定ユーティリティ
# ==================================================

def has_subject(text: str) -> bool:
    return bool(re.search(r"^件名[:：]", text.strip()))

def has_closing(text: str) -> bool:
    closing_keywords = [
        "以上",
        "よろしくお願いいたします",
        "ご報告申し上げます",
        "ご確認のほど",
    ]
    return any(k in text for k in closing_keywords)

# ==================================================
# メインAPI
# ==================================================

def apply_doc_template(text: str, rule_key: str) -> str:
    """
    文書本文にテンプレを安全に適用する
    - すでに件名があれば追加しない
    - すでに結びがあれば追加しない
    """

    template = DOC_TEMPLATES.get(rule_key, DOC_TEMPLATES["default"])
    lines = []

    body = text.strip()

    # ---- 件名 ----
    if not has_subject(body):
        lines.append(template["subject"])
        lines.append("")  # 空行

    # ---- 本文 ----
    lines.append(body)

    # ---- 結び ----
    if not has_closing(body):
        lines.append("")
        lines.append("――――――――――")
        lines.append(template["closing"])

    return "\n".join(lines)
