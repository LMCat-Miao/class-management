from fastapi import APIRouter, Depends, File, Form, UploadFile

from pydantic import BaseModel

from app.core.config import settings
from app.core.response import fail, ok
from app.deps import get_current_user
from app.services.file_content import FileContentError, validate_pdf_bytes

router = APIRouter(prefix="/ai", tags=["ai"])


class IntroBody(BaseModel):
    name: str
    keywords: list[str] | None = None
    category: str | None = None


class QuizBody(BaseModel):
    courseName: str | None = None
    topic: str | None = None
    count: int | None = 3


@router.post("/generate-intro")
def generate_intro(body: IntroBody, user: dict = Depends(get_current_user)):
    _ = user
    name = (body.name or "").strip()
    if not name:
        return fail("请输入课程名称")
    keywords = [k for k in (body.keywords or []) if k]
    keyword_text = "、".join(keywords) if keywords else "核心知识点与项目实践"
    category = body.category or "专业"
    intro = (
        f"本课程《{name}》面向{category}方向学习者，系统讲解{keyword_text}等相关内容。"
        "课程强调理论与实践结合，通过案例演练帮助学员掌握关键技术要点，"
        "提升解决实际问题的能力，适合希望快速建立完整知识体系并落地应用的同学。"
    )
    return ok({"intro": intro})


@router.post("/parse-pdf")
async def parse_pdf(
    file: UploadFile = File(...),
    courseName: str = Form(""),
    user: dict = Depends(get_current_user),
):
    """
    PDF 解析（教学助手桩实现）：先做大小与真实 PDF 内容校验，再返回兼容字段。
    不依赖客户端 Content-Type；不引入向量库/RAG。
    """
    _ = user
    file_name = (file.filename or "课程资料.pdf").strip() or "课程资料.pdf"
    # 仅取 basename，防路径干扰
    file_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    if not file_name.lower().endswith(".pdf"):
        return fail("仅支持 PDF 文件", status_code=400)

    max_bytes = int(settings.ai_pdf_max_bytes)
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        mb = max_bytes / (1024 * 1024)
        limit_text = f"{mb:.0f}MB" if mb >= 1 else f"{max_bytes}B"
        return fail(f"PDF 过大，上限 {limit_text}", status_code=400)
    try:
        validate_pdf_bytes(raw, require_eof=True)
    except FileContentError as exc:
        return fail(exc.message, status_code=exc.status_code)

    topic = (courseName or "").strip() or file_name[:-4]
    return ok(
        {
            "fileName": file_name,
            "summary": (
                f"已解析《{topic}》相关教学资料。文档围绕课程核心概念展开，"
                "涵盖基础理论、关键技术与实践案例，适合作为课堂教学与课后复习材料。"
            ),
            "knowledgePoints": [
                f"{topic} 基础概念与发展背景",
                "核心 API / 关键技术点",
                "常见业务场景与最佳实践",
                "项目实战与问题排查思路",
            ],
            "chapters": [
                f"第一章 {topic} 导论",
                "第二章 核心原理与基础用法",
                "第三章 进阶特性与工程化实践",
                "第四章 综合案例与总结",
            ],
            "focus": [
                "掌握核心概念与基本用法",
                "理解常见业务场景下的选型思路",
                "能够独立完成中小型实践项目",
            ],
            "difficulties": [
                "抽象概念理解与知识迁移",
                "工程化细节与性能优化",
                "复杂场景下的问题定位",
            ],
        }
    )


@router.post("/generate-quiz")
def generate_quiz(body: QuizBody, user: dict = Depends(get_current_user)):
    _ = user
    course_name = (body.courseName or body.topic or "").strip()
    if not course_name:
        return fail("请选择课程或输入主题")
    count = min(max(int(body.count or 3), 1), 5)
    topic = (body.topic or course_name).strip()

    choice = [
        {
            "id": i + 1,
            "type": "choice",
            "question": f"关于「{topic}」，下列说法正确的是？（第 {i + 1} 题）",
            "options": [
                "A. 只适用于理论学习，无法落地实践",
                "B. 需要结合具体业务场景理解与应用",
                "C. 与工程化无关，无需关注性能",
                "D. 以上都不对",
            ],
            "answer": "B",
        }
        for i in range(count)
    ]
    judge = [
        {
            "id": i + 1,
            "type": "judge",
            "question": (
                f"「{topic}」相关知识点可以直接照搬到所有项目中，"
                f"无需结合业务调整。（第 {i + 1} 题）"
            ),
            "answer": False,
        }
        for i in range(max(2, count - 1))
    ]
    short = [
        {
            "id": i + 1,
            "type": "short",
            "question": (
                f"请简述「{topic}」中的一个核心概念，并说明其在实际项目中的应用场景。"
                f"（第 {i + 1} 题）"
            ),
            "answer": (
                f"建议从概念定义、适用场景、注意事项三方面作答，"
                f"并结合《{course_name}》课程内容举例说明。"
            ),
        }
        for i in range(max(1, count - 2))
    ]
    return ok({"choice": choice, "judge": judge, "short": short})
