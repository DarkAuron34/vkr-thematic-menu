import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import HttpResponseForbidden, JsonResponse
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login

from .models import Dish, Profile, Restaurant, Menu, Theme, NationalCuisine, Difficulty, Ingredient, DishCategory, City
from .models import TemplateData, DishCategoriesData, filter_dishes_by_category, get_filtered_queryset, get_filtered_restaurants, filter_by_many_to_many_field
from .forms import DishForm, RegistrationForm, SearchForm, RestaurantSearchForm, OPTIONS_COOKING_TIME

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


class Option():
    def __init__(self, id, title, active=False):
        self.id = int(id)
        self.title = str(title)
        self.active = bool(active)


def _get_options(array):
    return [Option(x[0], x[1]) for x in array]


def _get_all_basic_template_data():
    data = TemplateData()
    data.ingredients = Ingredient.objects.all()
    data.themes = Theme.objects.all()
    data.difficulties = Difficulty.objects.all()
    data.national_cuisine = NationalCuisine.objects.all()
    data.restaurants = Restaurant.objects.all()
    data.cities = City.objects.all()
    data.dish_category = DishCategory.objects.all()
    data.menus = Menu.objects.all()
    data.dishes = Dish.objects.all()
    data.min_cooking_time_choices = _get_options(OPTIONS_COOKING_TIME)
    data.min_cooking_time_choices[0].active = True
    # data.min_cooking_time_choices.remove(data.min_cooking_time_choices[-1])
    data.max_cooking_time_choices = _get_options(OPTIONS_COOKING_TIME)
    data.max_cooking_time_choices[-1].active = True
    # data.max_cooking_time_choices.remove(data.max_cooking_time_choices[0])
    return data

def _filter_data(data, field_names: [str]):
    filtered_data = {}
    for i, x in zip(data.keys(), data.values()):
        if i in field_names:
            filtered_data.update({i: x})
    return filtered_data


def serialize_search_query(data) -> str:
    logger.debug(f"serializing data")
    new_data = {}
    for x, y in zip(data.keys(), data.values()):
        if x not in ["action"]:
            logger.debug(f"{x}: {y}")
            new_data.update({x: y})
        else:
            logger.debug(f"skipping {x}: {y}")
    res = json.dumps(new_data)
    logger.debug(f"finished serializing data")
    logger.debug(res)
    return res



def _get_active_menu(profile):
    try:
        return profile.active_menu.id
    except AttributeError:
        try:
            profile.active_menu = profile.menus.first()
            profile.save()
            return profile.active_menu.id
        except AttributeError:
            menu = Menu(user=profile.user, title="Новое меню")
            menu.save()
            menu.refresh_from_db()
            profile.active_menu = menu
            profile.save()
            return profile.active_menu.id


def _get_instances(model, numbers):
    return [model.objects.get(id=int(x)) for x in numbers]


@login_required
def menu(request):
    error = None
    user = request.user
    # create new menu and reload page
    if request.method == "GET" and len(request.GET) > 0:
        form = SearchForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            qs = Dish.objects.all()
            qs = get_filtered_queryset(qs, cleaned_data)
            max_dishes_in_category = cleaned_data['max_dishes_in_category']
            if max_dishes_in_category is None or max_dishes_in_category < 1:
                max_dishes_in_category = 3
            filtered_dishes = DishCategoriesData(qs)
            filtered_dishes.fix_dishes(max_dishes_in_category)
            qs = Dish.objects.all().filter(id__in=[x.id for x in filtered_dishes.get_dishes()])
            search_query = serialize_search_query(cleaned_data)
            qs = qs.order_by("?")
            if user.is_authenticated:
                menu = Menu(
                    title=f"Автоматически сгенерированное меню для {user.username}", user=user, search_query=search_query)
            else:
                menu = Menu(
                    title=f"Автоматически сгенерированное меню")
            menu.save()
            menu.dishes.set(qs)
            menu.refresh_from_db()
            request.user.profile.active_menu = menu
            user.profile.save()
            return redirect("/menu/")
        else:
            error = "Проверьте правильность введенных данных."

    # display existing active menu or none
    data = _get_all_basic_template_data()
    active_menu = user.profile.active_menu
    if active_menu:
        menu = active_menu
        categories = filter_dishes_by_category(menu.dishes)
    else:
        menu = None
        categories = None
    context = {'title': f'Меню',
               "error": error,
               "menu": menu,
               "categories": categories,
               "data": data}
    return render(request, 'main/menu.html', context)


def search(request):
    if request.method == "GET" and len(request.GET) > 0:
        form = SearchForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            qs = Dish.objects.all()
            qs = get_filtered_queryset(qs, cleaned_data)
        else:
            qs = Dish.objects.all()
            error = "Проверьте введенные данные."
    else:
        qs = Dish.objects.all()
    error = None
    data = _get_all_basic_template_data()
    context = {'title': f'Главная страница сайта',
               "error": error,
               "dishes": qs,
               "data": data}
    return render(request, 'main/search.html', context)


@login_required
def active_menu(request):
    profile = request.user.profile
    pk = _get_active_menu(profile)
    return menu_update(request, pk)


@login_required
def active_menu_set(request):
    profile = request.user.profile
    menu = request.user.menu_set.get(id=request.GET['menu_id'])
    profile.active_menu = menu
    profile.save()
    return redirect('/active_menu')


def restaurants(request):
    error = None
    if request.method == "GET" and len(request.GET) > 0:
        form = RestaurantSearchForm(request.GET)
        if form.is_valid():
            qs = get_filtered_restaurants(form.cleaned_data)
    else:
        qs = Restaurant.objects.all()
    data = _get_all_basic_template_data()
    context = {'title': 'Поиск ресторанов', 'restaurants': qs, 'data': data}
    return render(request, 'main/restaurants.html', context)


def restaurant_details(request, pk):
    restaurant = get_object_or_404(Restaurant, id=pk)
    context = {'title': f'Информация о ресторане "{restaurant.title}"', 'restaurant': restaurant}
    return render(request, 'main/restaurant_details.html', context)


def dish(request, pk):
    dish = get_object_or_404(Dish, id=pk)
    context = {'title': f'Страница рецепта "{dish.title}"', "dish": dish}
    return render(request, 'main/dish.html', context)


@login_required
def dish_create(request):
    template_data = _get_all_basic_template_data()
    error = None
    if request.method == "POST":
        form = DishForm(request.POST)
        if form.is_valid():
            data = {
                'user':                 request.user,
                'title':                form.cleaned_data['title'],
                'description':          form.cleaned_data['description'],
                'cooking_time':         form.cleaned_data['cooking_time'],
                'difficulty':           Difficulty.objects.get(id=int(form.cleaned_data['difficulty'])),
                'category':             DishCategory.objects.get(id=int(form.cleaned_data['dish_category'])),
                'national_cuisine':     NationalCuisine.objects.get(id=int(form.cleaned_data['national_cuisine'])),
            }
            instance = Dish(**data)
            instance.save()
            instance.ingredients.set(_get_instances(
                Ingredient, form.cleaned_data['ingredients']))
            instance.themes.set(_get_instances(
                Theme, form.cleaned_data['themes']))
            # instance.image.url = form.cleaned_data['image']
            instance.save()
            instance.refresh_from_db()
            return redirect(f"/dish/{instance.id}")
        else:
            error = form.errors
    context = {'title': f'Новый рецепт', "error": error, "data": template_data}
    return render(request, 'main/dish_update.html', context)


def about(request):
    context = {'title': 'Страница о нас'}
    return render(request, 'main/about.html', context)


def registration(request):
    error = None
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.save()
            profile = Profile(user=user)
            profile.save()
            user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, user)
            return redirect('/')
        else:
            error = "Проверьте правильность введенных данных."
    data = {
        'error': error,
        'title': 'Страница регистрации'}
    return render(request, 'main/registration.html', data)

@login_required
def profile(request):
    user = request.user
    context = {'title': f'Профиль пользователя {user.username}',
               'user': user,}
    return render(request, 'main/profile.html', context)



"/favorites/?type=dish&id=1&action=add"
@login_required
def favorites(request):
    _MODELS = {
        'dish': Dish,
        'restaurant': Restaurant,
        'menu': Menu
    }
    model = _MODELS[request.GET['type']]
    object_id = int(request.GET['id'])
    profile = request.user.profile
    instance = get_object_or_404(model, id=object_id)

    if request.GET['type'] == "dish":
        favorites = profile.favorite_dishes
        redirect_page = '/'
    elif request.GET['type'] == "restaurant":
        favorites = profile.favorite_restaurants
        redirect_page = '/restaurants/'
    elif request.GET['type'] == "menu":
        redirect_page = '/menu/'
        favorites = profile.favorite_menus
    else:
        raise ValueError

    if request.GET['action'] == 'add':
        favorites.add(instance)
    elif request.GET['action'] == 'remove':
        favorites.remove(instance)
    else:
        raise ValueError

    instance.save()
    profile.save()
    return redirect(redirect_page)


@login_required
def active_menu_remove(request):
    profile = request.user.profile
    profile.active_menu = None
    profile.save()
    return redirect('/menu/')

def active_menu_set(request):
    profile = request.user.profile
    menu_id = request.GET['id']
    menu = Menu.objects.get(id=menu_id)
    profile.active_menu = menu
    profile.save()
    return redirect('/menu/')

"/active_menu/edit/?id=1&action=add"
@login_required
def active_menu_edit(request):
    profile = request.user.profile
    menu = profile.active_menu
    object_id = request.GET.get('dish')
    instance = get_object_or_404(Dish, id=object_id)
    if request.GET['action'] == 'add':
        menu.dishes.add(instance)
    elif request.GET['action'] == 'remove':
        menu.dishes.remove(instance)
    elif request.GET['action'] == 'replace':
        menu.replace_dish(instance)
    elif request.GET['action'] == 'delete':
        profile.active_menu = None
    profile.save()
    menu.save()
    return redirect('/menu/#active-menu')