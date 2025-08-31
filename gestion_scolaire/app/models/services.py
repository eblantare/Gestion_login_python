from extensions import db,BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Service(BaseModel):
    __tablename__ = 'services'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    code = db.Column(db.String(50),unique=True, nullable=False)
    libelle = db.Column(db.String(200), nullable=False)
    