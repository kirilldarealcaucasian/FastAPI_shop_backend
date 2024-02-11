"""delete unqiue constraint on Image (product_id)

Revision ID: 7dc902eaec0f
Revises: ebd024c195f1
Create Date: 2024-02-09 15:58:39.518274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dc902eaec0f'
down_revision: Union[str, None] = 'ebd024c195f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('images_product_id_key', 'images', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('images_product_id_key', 'images', ['product_id'])
    # ### end Alembic commands ###