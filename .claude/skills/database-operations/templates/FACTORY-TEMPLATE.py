# Factory テンプレート
# 参考: api/src/models/tickets/factories.py

from factory import Faker

from src.models.factories.base import BaseFactory
from src.models.models.models import Model


class ModelFactory(BaseFactory[Model]):
    _exclude_fields = {
        "id",
        "created_at",
        "updated_at",
        "user_id",
    }

    class Meta:
        model = Model

    title: str = Faker("sentence", nb_words=4)  # type: ignore[assignment]
    description: str = Faker("text", max_nb_chars=200)  # type: ignore[assignment]


# Faker パターン例
# Faker("sentence", nb_words=4)      # タイトル
# Faker("text", max_nb_chars=200)    # 説明文
# Faker("email")                     # メール
# Faker("name")                      # 名前
# Faker("url")                       # URL
# Faker("date_time")                 # 日時
