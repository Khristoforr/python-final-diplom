from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from api.models import User, ConfirmEmailToken
from orders import settings


@shared_task
def new_order_task(user_id, **kwargs):
    user = User.objects.get(id=user_id)
    msg = EmailMultiAlternatives(
        # title:
        "Cпасибо за заказ",
        # message:
        f'Номер вашего заказа: {kwargs["order_id"]}\n'
        f'Наш оператор свяжется с Вами в ближайшее время для уточнения деталей заказа.'
        f'Статус заказов вы можете посмотреть в разделе "Заказы"',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()


@shared_task
def new_user_registered_task(user_id, **kwargs):
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
    msg = EmailMultiAlternatives(
        # title:
        f"Token for confirm registration {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()
