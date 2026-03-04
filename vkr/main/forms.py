import logging

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.utils import OperationalError

from .models import Dish, Difficulty, Theme, Ingredient, NationalCuisine, DishCategory, City


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# logging.basicConfig(level=logging.ERROR)


def _get_iterable(model, attr):
    try:
        iter = []
        iter.extend([(x.id, getattr(x, attr)) for x in model.objects.all()])
    except OperationalError:
        iter = []
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Generating choices for {model}, field {attr}")
        logger.debug(f"objects: {[(i, x.id, x) for i, x in enumerate(model.objects.all())]}")
        logger.debug(f"choices: {iter}")
    return iter

OPTIONS_COOKING_TIME = [
    (0, "Менее 20 мин."),
    (20, "20 мин."),
    (40, "40 мин."),
    (60, "60 мин."),
    (80, "Более 60 мин."),
]


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class DishForm(forms.Form):
    title = forms.CharField(label="", max_length=255, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Название'}))
    description = forms.CharField(label="", max_length=255, required=True, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Описание'}))
    cooking_time = forms.IntegerField(label="", min_value=0, required=True, widget=forms.widgets.NumberInput(
        attrs={'min': 0, 'placeholder': 'Время готовки'}))

    ingredients = forms.MultipleChoiceField(
        label="Ингридиенты", choices=_get_iterable(Ingredient, "title"), required=False)
    difficulty = forms.ChoiceField(
        label="Сложность", initial=None, choices=_get_iterable(Difficulty, "title"), required=True)
    national_cuisine = forms.ChoiceField(
        label="Кухня", initial=None, choices=_get_iterable(NationalCuisine, "title"), required=False)
    themes = forms.MultipleChoiceField(
        label="Темы", choices=_get_iterable(Theme, "title"), required=False)
    dish_category = forms.ChoiceField(label="Категория блюд",
                                   initial=None, choices=_get_iterable(DishCategory, "title"), required=False)
    image = forms.ImageField(required=False)


class SearchForm(forms.Form):
    text = forms.CharField(label="", max_length=255, required=False, widget=forms.widgets.TextInput(
        attrs={'placeholder': 'Название и описание'}))
    min_price = forms.IntegerField(label="", min_value=0, required=False, widget=forms.widgets.NumberInput(
        attrs={'min': 0, 'placeholder': 'Мин. цена'}))
    max_price = forms.IntegerField(label="", required=False, widget=forms.widgets.NumberInput(
        attrs={'min': 0, 'placeholder': 'Макс. цена'}))
    min_cooking_time = forms.ChoiceField(label="", choices=OPTIONS_COOKING_TIME, required=False)
    max_cooking_time = forms.ChoiceField(label="", choices=OPTIONS_COOKING_TIME, required=False)

    difficulty = forms.MultipleChoiceField(label="Сложность",
                                   initial=None, choices=_get_iterable(Difficulty, "title"), required=False)
    dish_category = forms.MultipleChoiceField(label="Категория блюд",
                                   initial=None, choices=_get_iterable(DishCategory, "title"), required=False)
    max_dishes_in_category = forms.IntegerField(label="Кол-во блюд в категории блюд", required=False)
    national_cuisine = forms.MultipleChoiceField(
        label="Кухня", choices=_get_iterable(NationalCuisine, "title"), required=False)
    ingredients = forms.MultipleChoiceField(
        label="Ингридиенты", choices=_get_iterable(Ingredient, "title"), required=False)
    ignore_ingredients = forms.MultipleChoiceField(
        label="Игнорировать ингридиенты", choices=_get_iterable(Ingredient, "title"), required=False)
    themes = forms.MultipleChoiceField(label="Темы", choices=_get_iterable(
        Theme, "title"), required=False)


class RestaurantSearchForm(forms.Form):
    national_cuisine = forms.MultipleChoiceField(
        label="Кухня", choices=_get_iterable(NationalCuisine, "title"), required=False)
    themes = forms.MultipleChoiceField(label="Тематика", choices=_get_iterable(
        Theme, "title"), required=False)
    city = forms.MultipleChoiceField(label="Город", choices=_get_iterable(
        City, "name"), required=False)