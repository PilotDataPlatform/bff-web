from pydantic import BaseModel


class CreateResourceRequest(BaseModel):
    project_id: str
    request_for: str
