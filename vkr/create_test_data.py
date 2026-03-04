# import django.contrib.auth.models as authModels
import main.models as mainModels

def simple_create(model, names: list):
    for name in names:
        m = model(title=str(name))
        m.save()

simple_create(mainModels.Difficulty, ["Легко","Средне","Сложно"])
simple_create(mainModels.Theme, ["Простая еда","Норм еда","Так себе"])
simple_create(mainModels.NationalCuisine, ["Кухня " + str(i) for i in range(10)])