from typing import Literal

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    username: str


class GoogleLoginRequest(BaseModel):
    token: str  # Google ID token from OAuth callback


class SaveChapterRequest(BaseModel):
    class_name: str
    subject: str
    chapter: str
    content: str
    username: str


class QuestionRowConfig(BaseModel):
    questionType: str  # "mcq", "short", or "long"
    questionCount: int
    marksPerQuestion: float


class GenerateQuestionsRequest(BaseModel):
    class_name: str
    subject: str
    chapters: list[str]  # Changed from single chapter to list of chapters
    assessmentCategory: str  # "fa" or "sa"
    assessmentNumber: int    # 1 or 2
    complexity: Literal["basic", "intermediate", "advanced"]
    questionRows: list[QuestionRowConfig]
    username: str


class SaveUploadedQuestionsRequest(BaseModel):
    class_name: str
    subject: str
    chapters: list[str]
    assessmentCategory: str  # "fa" or "sa"
    assessmentNumber: int    # 1 or 2
    complexity: Literal["basic", "intermediate", "advanced"]
    paperContent: str  # Previously scanned/edited question paper text
    questionRows: list[QuestionRowConfig]
    username: str
