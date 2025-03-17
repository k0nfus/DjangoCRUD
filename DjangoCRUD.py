import os
import django
import sys
from django.apps import apps

# Automatische Erkennung des Django-Projektnamens
def find_django_project():
    current_dir = os.path.abspath(os.path.dirname(__file__))  # Aktuelles Verzeichnis
    while current_dir != os.path.dirname(current_dir):  # Stoppt, wenn Root erreicht
        if "manage.py" in os.listdir(current_dir):  # Suche nach manage.py
            return os.path.basename(current_dir)
        current_dir = os.path.dirname(current_dir)  # Gehe ein Verzeichnis höher
    raise FileNotFoundError("Kein Django-Projekt mit 'manage.py' gefunden.")

# Projektname automatisch setzen
PROJECT_NAME = find_django_project()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{PROJECT_NAME}.settings')
django.setup()

# App-Namen aus aktuellem Verzeichnis holen
APP_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

print(f"📌 Django-Projekt erkannt: {PROJECT_NAME}")
print(f"📌 Generiere CRUD für die App: {APP_NAME}")

# Verzeichnis-Pfade
TEMPLATES_DIR = os.path.join(APP_NAME, "templates", APP_NAME)
VIEWS_PATH = os.path.join(APP_NAME, "views.py")
FORMS_PATH = os.path.join(APP_NAME, "forms.py")
URLS_PATH = os.path.join(APP_NAME, "urls.py")

# Sicherstellen, dass das Template-Verzeichnis existiert
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Alle Models der App holen
models_module = apps.get_app_config(APP_NAME).models

# 🛠 Helper-Funktion zum Erstellen von Dateien 🛠
def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# CRUD-Templates generieren
for model_name, model in models_module.items():
    model_name_lower = model_name.lower()

    # Template: LIST
    list_template = f"""
    {{% extends 'base.html' %}}

    {{% block title %}}{model_name} Liste{{% endblock %}}

    {{% block content %}}
    <h2>{model_name} Liste</h2>
    <form method="GET">
        {{% for field in object_list.0._meta.fields %}}
        <input type="text" name="{{{{ field.name }}}}" placeholder="{{{{ field.verbose_name }}}}">
        {{% endfor %}}
        <button type="submit">Filtern</button>
    </form>
    <ul>
        {{% for obj in object_list %}}
            <li><a href="{{{{ obj.get_absolute_url }}}}">{{{{ obj }}}}</a></li>
        {{% empty %}}
            <li>Keine Einträge vorhanden.</li>
        {{% endfor %}}
    </ul>
    <a href="{{% url '{APP_NAME}:{model_name_lower}_create' %}}">Neues {model_name} erstellen</a>
    {{% endblock %}}
    """
    write_file(os.path.join(TEMPLATES_DIR, f"{model_name_lower}_list.html"), list_template)

    # Template: DETAIL
    detail_template = f"""
    {{% extends 'base.html' %}}

    {{% block title %}}{model_name} Detail{{% endblock %}}

    {{% block content %}}
    <h2>{model_name} Detail</h2>
    {{% for field in object._meta.fields %}}
        <p><strong>{{{{ field.verbose_name }}}}:</strong> {{{{ object|attr:field.name }}}}</p>
    {{% endfor %}}
    <a href="{{% url '{APP_NAME}:{model_name_lower}_update' object.pk %}}">Bearbeiten</a>
    <a href="{{% url '{APP_NAME}:{model_name_lower}_delete' object.pk %}}">Löschen</a>
    {{% endblock %}}
    """
    write_file(os.path.join(TEMPLATES_DIR, f"{model_name_lower}_detail.html"), detail_template)

    # Template: FORM
    form_template = f"""
    {{% extends 'base.html' %}}

    {{% block title %}}{model_name} Formular{{% endblock %}}

    {{% block content %}}
    <h2>{model_name} Formular</h2>
    <form method="POST">
        {{% csrf_token %}}
        {{{{ form.as_p }}}}
        <button type="submit">Speichern</button>
    </form>
    {{% endblock %}}
    """
    write_file(os.path.join(TEMPLATES_DIR, f"{model_name_lower}_form.html"), form_template)

    # Template: CONFIRM DELETE
    delete_template = f"""
    {{% extends 'base.html' %}}

    {{% block title %}}{model_name} löschen{{% endblock %}}

    {{% block content %}}
    <h2>{model_name} wirklich löschen?</h2>
    <form method="POST">
        {{% csrf_token %}}
        <button type="submit">Löschen</button>
    </form>
    {{% endblock %}}
    """
    write_file(os.path.join(TEMPLATES_DIR, f"{model_name_lower}_confirm_delete.html"), delete_template)

# Forms generieren
forms_content = "from django import forms\nfrom .models import *\n\n"
for model_name in models_module.keys():
    forms_content += f"class {model_name}Form(forms.ModelForm):\n"
    forms_content += f"    class Meta:\n        model = {model_name}\n        fields = '__all__'\n\n"
write_file(FORMS_PATH, forms_content)

# Views generieren
views_content = "from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView\n"
views_content += "from django.urls import reverse_lazy\nfrom .models import *\nfrom .forms import *\n\n"

for model_name in models_module.keys():
    model_name_lower = model_name.lower()
    views_content += f"""
class {model_name}ListView(ListView):
    model = {model_name}
    template_name = '{APP_NAME}/{model_name_lower}_list.html'
    context_object_name = 'object_list'

class {model_name}DetailView(DetailView):
    model = {model_name}
    template_name = '{APP_NAME}/{model_name_lower}_detail.html'

class {model_name}CreateView(CreateView):
    model = {model_name}
    form_class = {model_name}Form
    template_name = '{APP_NAME}/{model_name_lower}_form.html'

class {model_name}UpdateView(UpdateView):
    model = {model_name}
    form_class = {model_name}Form
    template_name = '{APP_NAME}/{model_name_lower}_form.html'

class {model_name}DeleteView(DeleteView):
    model = {model_name}
    template_name = '{APP_NAME}/{model_name_lower}_confirm_delete.html'
    success_url = reverse_lazy('{APP_NAME}:{model_name_lower}_list')
"""
write_file(VIEWS_PATH, views_content)

# URLs generieren
urls_content = "from django.urls import path\nfrom .views import *\n\n"
urls_content += f"app_name = '{APP_NAME}'\n\nurlpatterns = [\n"

for model_name in models_module.keys():
    model_name_lower = model_name.lower()
    urls_content += f"    path('{model_name_lower}/', {model_name}ListView.as_view(), name='{model_name_lower}_list'),\n"
    urls_content += f"    path('{model_name_lower}/<int:pk>/', {model_name}DetailView.as_view(), name='{model_name_lower}_detail'),\n"
urls_content += "]\n"
write_file(URLS_PATH, urls_content)

print(f"CRUD für die App '{APP_NAME}' erfolgreich generiert!")
