from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    username: str


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
    chapter: str
    questionRows: list[QuestionRowConfig]
    username: str
