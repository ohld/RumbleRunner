# 2022-01-22 20:41:57.354514
from alembic import op
import sqlalchemy as sa

revision = '237ade2740e0'
down_revision = '7a1702e73d8f'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('telegram_user_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_message_id', sa.BigInteger(), nullable=True))

    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('telegram_user_request', schema=None) as batch_op:
        batch_op.drop_column('original_message_id')

    # ### end Alembic commands ###
