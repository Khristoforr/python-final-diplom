from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
# from api.signals import create_auth_token

STATUS_CHOICES = [
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Укомплектован'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
]

CONTACT_TYPE_CHOICES = [
    ('phone', 'Номер телефона'),
    ('address', 'Адрес'),
]

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    url = models.URLField(unique=True, verbose_name='Ссылка')
    filename = models.FileField(upload_to='Shops', verbose_name='Файл с товарами магазина', blank=True, null=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True, verbose_name='Магазины')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.SET_DEFAULT,
                                 default="Товар без категории", related_name='products')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = "Список товаров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', related_name='products_info')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин')
    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)
    quantity = models.IntegerField()
    price = models.IntegerField()
    price_rrc = models.IntegerField()

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Информационный список о продуктах"
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info'),
        ]


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')

    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = "Список параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                     related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, verbose_name='Параметр товара',
                                  related_name='product_parameters')
    value = models.CharField(max_length=120, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров товара"
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]


class Order(models.Model):
    user = models.ForeignKey('User', verbose_name='Пользователь',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, verbose_name='Статус', choices=STATUS_CHOICES)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"
        ordering = ('-dt',)

    def __str__(self):
        return f'Заказ №{self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE, related_name='ordered_items')
    product = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', on_delete=models.CASCADE,
                                related_name='ordered_items')
    quantity = models.IntegerField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product'], name='unique_order_item'),
        ]


class Contact(models.Model):
    type = models.CharField(max_length=10, verbose_name='Тип контактных данных', choices=CONTACT_TYPE_CHOICES)
    user = models.ForeignKey('User', verbose_name='Пользователь',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    value = models.CharField(max_length=100, verbose_name='Данные')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.user.name} - {self.value}'