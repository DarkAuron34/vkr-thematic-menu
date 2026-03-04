import json
import logging

from django.db import models
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


class TemplateData():
    pass


def get_filtered_restaurants(data):
    qs = Restaurant.objects.all()
    qs = filter_by_many_to_many_field(qs, Theme, data["themes"], "themes")
    qs = filter_by_many_to_many_field(qs, City, data["city"], "city")
    qs = filter_by_many_to_many_field(
        qs, NationalCuisine, data["national_cuisine"], "national_cuisine")
    return qs


def filter_by_many_to_many_field(qs, model, data, field_name):
    try:
        try:
            if data[0] != "0":
                x = model.objects.filter(id__in=[int(x) for x in data])
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("filtering by " + field_name)
                    logger.debug(f"value is {data}")
                    logger.debug(f"value (unwrap) is {x}")
                kwargs = {str(field_name) + "__in": x}
                qs = qs.filter(**kwargs)
        except MultiValueDictKeyError:
            pass
    except IndexError:
        pass
    return qs


def get_filtered_queryset(qs: list, data: dict):
    logger.debug(f"started filtering, {len(qs)} dishes")
    if data['text'] != "":
        logger.debug("filtering by text")
        qs = qs.filter(title__contains=data['text']) | qs.filter(
            description__contains=data['text'])
    if data['min_price']:
        logger.debug("filtering by min price")
        qs = qs.filter(price__gte=data['min_price'])
    if data['max_price']:
        logger.debug("filtering by max price")
        qs = qs.filter(price__lte=data['max_price'])
    if data['min_cooking_time']:
        logger.debug("filtering by min. cooking time")
        min_cooking_time = int(data['min_cooking_time'])
        if min_cooking_time < 80:
            qs = qs.filter(cooking_time__gte=min_cooking_time)
        else:
            raise ValueError
    if data['max_cooking_time']:
        logger.debug("filtering by max. cooking time")
        max_cooking_time = int(data['max_cooking_time'])
        if max_cooking_time > 20:
            qs = qs.filter(cooking_time__lte=max_cooking_time)
        else:
            raise ValueError
    if data['national_cuisine']:
        logger.debug("filtering by national cuisine")
        qs = qs.filter(national_cuisine__in=[int(x)
                       for x in data['national_cuisine']])
    if data['dish_category']:
        logger.debug("filtering by dish_category")
        qs = qs.filter(category__in=[int(x)
                       for x in data['dish_category']])
    qs = filter_by_many_to_many_field(qs, Theme, data["themes"], "themes")
    qs = filter_by_many_to_many_field(
        qs, Difficulty, data["difficulty"], "difficulty")
    qs = filter_by_many_to_many_field(
        qs, Ingredient, data["ingredients"], "ingredients")
    if data['ignore_ingredients']:
        qs_ignore = filter_by_many_to_many_field(
            qs, Ingredient, data['ignore_ingredients'], "ingredients")
        qs = qs.exclude(id__in=qs_ignore)
    logger.debug(f"finished filtering, {len(qs)} dishes")
    return qs


class DishCategoryData(TemplateData):
    def fix_dishes(self, count):
        length = len(self.dishes)
        if length > count:
            self.dishes = self.dishes[:count]


class DishCategoriesData(TemplateData):
    def fix_dishes(self, count):
        for x in self.categories:
            x.fix_dishes(count)

    def get_dishes(self):
        qs = []
        for x in self.categories:
            qs.extend(x.dishes)
        return qs

    def __init__(self, dishes):
        self.categories = filter_dishes_by_category(dishes)


def filter_dishes_by_category(dishes: []) -> list[TemplateData]:
    logger.debug(f"Filtering {dishes} by categories.")

    def check_if_category_exists_and_create(categories: list[TemplateData], category: DishCategory):
        for existing_category in categories:
            if category.id == existing_category.id:
                return existing_category
        category_template_data = DishCategoryData()
        category_template_data.id = category.id
        category_template_data.title = category.title
        category_template_data.dishes = []
        categories.append(category_template_data)
        return categories[-1]
    categories = []
    for dish in dishes.all():
        category = check_if_category_exists_and_create(
            categories, dish.category)
        category.dishes.append(dish)
    logger.debug(f"Finished filtering: {categories}")
    for x in categories:
        logger.debug(f"{x.title}")
        logger.debug(f"{x.dishes}")
    return categories


def check_categories(qs: list) -> None:
    categories = filter_dishes_by_category(qs)
    for x in categories:
        if len(x.dishes) > 3:
            raise ValueError


class Ingredient(models.Model):
    title = models.CharField('Название', max_length=255)
    price = models.PositiveIntegerField('Цена')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class DishCategory(models.Model):
    title = models.CharField('Название', max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория блюд'
        verbose_name_plural = 'Категории блюд'


class Difficulty(models.Model):
    title = models.CharField('Название', max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Сложность'
        verbose_name_plural = 'Сложности'


class NationalCuisine(models.Model):
    title = models.CharField('Название', max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Национальная кухня'
        verbose_name_plural = 'Национальные кухни'


class Theme(models.Model):
    title = models.CharField('Название', max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тематика'
        verbose_name_plural = 'Тематики'


class City(models.Model):
    name = models.CharField('Название', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class Dish(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    title = models.CharField('Название', max_length=255)
    description = models.CharField(
        'Описание', max_length=500, blank=True, null=True)
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')

    difficulty = models.ForeignKey(
        Difficulty, blank=True, null=True, verbose_name="Сложность приготовления", on_delete=models.CASCADE)
    national_cuisine = models.ForeignKey(
        NationalCuisine, blank=True, null=True, verbose_name='Национальная кухня', on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        Ingredient, blank=True, verbose_name='Ингредиенты блюда')
    themes = models.ManyToManyField(Theme, blank=True, verbose_name="Тематики")
    category = models.ForeignKey(
        DishCategory, verbose_name='Категория блюд', blank=True, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(blank=True, null=True, upload_to='images/')

    price = models.PositiveIntegerField(verbose_name='Цена', default=120)

    # @property
    # def price(self):
    #     sum = 0
    #     for x in self.ingredients.all():
    #         sum += x.price
    #     return sum

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'


class Restaurant(models.Model):
    title = models.CharField('Название', max_length=255)
    city = models.ForeignKey(City, verbose_name='Город', default=None,
                             blank=True, null=True, on_delete=models.SET_NULL)
    district = models.CharField('Район', max_length=255)
    address = models.CharField('Адрес', max_length=255)
    description = models.CharField(
        'Описание', max_length=500, blank=True, null=True)

    themes = models.ManyToManyField(Theme, verbose_name='Тематики')
    national_cuisine = models.ManyToManyField(
        NationalCuisine, verbose_name='Кухни')
    image = models.ImageField(blank=True, null=True, upload_to='images/')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Ресторан'
        verbose_name_plural = 'Рестораны'


class Menu(models.Model):
    user = models.ForeignKey(User, models.CASCADE, null=True, blank=True)
    title = models.CharField(verbose_name="Название меню",
                             blank=False, null=False, max_length=255)
    dishes = models.ManyToManyField(Dish, verbose_name='Блюда')
    temporary_id = models.IntegerField(
        auto_created=True, default=-1, null=True, blank=True)

    # json serialized data
    search_query = models.CharField(
        default="{}", blank=False, null=False, max_length=10000)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Меню'
        verbose_name_plural = 'Меню'

    def replace_dish(self, dish: Dish) -> Dish:
        def get_category_and_dish(categories, dish_id):
            for cat in categories:
                for dish in cat.dishes:
                    if dish.id == dish_id:
                        return (cat, dish)
            raise ValueError

        dish_id = dish.id
        categories = filter_dishes_by_category(self.dishes)

        # find dish to replace
        # find category to be updated
        cat, dish = get_category_and_dish(categories, dish_id)

        # get new qs
        search_query = json.loads(self.search_query)
        new_dishes = get_filtered_queryset(Dish.objects.all(), search_query)
        new_dishes.exclude(id=dish.id)
        new_dishes = new_dishes.order_by("?")
        new_dishes_categories = filter_dishes_by_category(new_dishes)

        # get new category with same id
        for x in new_dishes_categories:
            if x.id == cat.id:
                new_dishes_cat = x
                break

        dish_to_add = None
        # get new dish but ignore dishes that are already in menu
        for x in new_dishes_cat.dishes:
            if x not in cat.dishes:
                dish_to_add = x
        if dish_to_add == None:
            return

        self.dishes.add(dish_to_add)
        self.dishes.remove(dish)
        check_categories(self.dishes)
        self.save()
        return dish_to_add

    def short_description(self):
        return str(self.description[0:200])


class Profile(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    active_menu = models.ForeignKey(Menu, related_name="active_manu",
                                    default=None, on_delete=models.SET_NULL, blank=True, null=True)
    favorite_dishes = models.ManyToManyField(
        Dish, blank=True, verbose_name='Избранные блюда')
    favorite_menus = models.ManyToManyField(
        Menu, blank=True, verbose_name='Избранные меню')
    favorite_restaurants = models.ManyToManyField(
        Restaurant, blank=True, verbose_name='Избранные рестораны')

    def __str__(self):
        return "Профиль пользователя " + str(self.user)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


MODELS = [Dish, Ingredient, Difficulty, DishCategory,
          NationalCuisine, Theme, Menu,
          Restaurant, City, Profile]
