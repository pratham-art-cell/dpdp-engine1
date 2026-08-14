from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, ConfigDict

# SQLModel: Maps to the database table
class Lab(SQLModel, table=True):
    __tablename__ = "labs"

    id: Optional[int] = Field(default=None, primary_key=True)
    lab_name: str = Field(index=True)
    uses_paper_ledgers: bool = Field(default=False)
    has_digital_consent_logs: bool = Field(default=True)
    compliance_status: str = Field(default="Pending")

# Pydantic Schema: Validates incoming HTMX form data
class LabCreate(BaseModel):
    lab_name: str
    uses_paper_ledgers: bool
    has_digital_consent_logs: bool

    model_config = ConfigDict(extra="forbid")