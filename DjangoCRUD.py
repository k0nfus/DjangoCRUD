import os
import re

# Automatisch den App-Namen erkennen
APP_PATH = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(APP_PATH)

# Pfad zur models.py
MODELS_PATH = os.path.join(APP_PATH, "models.py")

# Templates-Ordner für die App (korrekt setzen)
TEMPLATES_DIR = os.path.join(APP_PATH, "templates", APP_NAME)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Wichtige Datei-Pfade
VIEWS_PATH = os.path.join(APP_PATH, "views.py")
URLS_PATH = os.path.join(APP_PATH, "urls.py")
FORMS_PATH = os.path.join(APP_PATH, "forms.py")
BASE_HTML_PATH = os.path.join(TEMPLATES_DIR, "base.html")

# Funktion zum Erstellen von Dateien
def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# `models.py` als TEXT lesen und Modelle extrahieren
def extract_models():
    if not os.path.exists(MODELS_PATH):
        print("❌ Fehler: models.py nicht gefunden!")
        return {}

    with open(MODELS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    model_pattern = re.findall(r"class\s+(\w+)\(models\.Model\):", content)
    field_pattern = re.findall(r"class\s+(\w+)\(models\.Model\):([\s\S]*?)(?=\nclass|\Z)", content)

    models = {}

    for model_name, model_body in field_pattern:
        field_matches = re.findall(r"(\w+)\s*=\s*models\.(\w+)\(", model_body)
        models[model_name] = [(field, field_type) for field, field_type in field_matches]

    return models

# Models auslesen
models = extract_models()

print(f"Gefundene Modelle in {APP_NAME}: {', '.join(models.keys())}")

# `base.html` generieren (Dark-Mode mit Bootstrap & JS für Dropdowns)
if not os.path.exists(BASE_HTML_PATH):
    base_html = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{% block title %}Django App{% endblock %}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            body { background-color: #121212; color: #e0e0e0; }
            .navbar-dark .navbar-nav .nav-link { color: #ffffff; }
            .dropdown-menu { background-color: #333333; }
            .dropdown-item { color: #e0e0e0; }
            .dropdown-item:hover { background-color: #444444; }
            .table-dark { background-color: #222222; }
        </style>
    </head>
    <body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{% url 'index' %}">Home</a>
        </div>
    </nav>
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    </body>
    </html>
    """
    write_file(BASE_HTML_PATH, base_html)
    print("`base.html` wurde erstellt.")

# CRUD-Templates generieren
for model_name, fields in models.items():
    model_name_lower = model_name.lower()

    # 🔹 List View mit Filter-Formular
    field_headers = "".join([f"<th>{field[0]}</th>" for field in fields])
    field_cells = "".join([f"<td>{{{{ obj.{field[0]} }}}}</td>" for field in fields])

    list_template = f"""
    {{% extends 'base.html' %}}

    {{% block title %}}{model_name} Liste{{% endblock %}}

    {{% block content %}}
    <h2>{model_name} Liste</h2>
    
    <!-- Filterbereich -->
    <button class="btn btn-secondary mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#filterCollapse">
        Filter ein-/ausklappen
    </button>

    <div class="collapse" id="filterCollapse">
        <form method="get" class="mb-3">
            {{% for field in form.visible_fields %}}
                <div class="mb-2">{{{{ field.label }}}}: {{{{ field }}}}</div>
            {{% endfor %}}
            <button type="submit" class="btn btn-primary">Filtern</button>
        </form>
    </div>

    <a href="{{{{% url '{APP_NAME}:{model_name_lower}_create' %}}}}" class="btn btn-success">Neuen Eintrag erstellen</a>

    <table class="table table-dark table-striped mt-3">
        <thead>
            <tr>{field_headers}<th>Aktionen</th></tr>
        </thead>
        <tbody>
        {{% for obj in object_list %}}
            <tr>
                {field_cells}
                <td>
                    <a href="{{{{% url '{APP_NAME}:{model_name_lower}_detail' obj.pk %}}}}" class="btn btn-sm btn-info">Details</a>
                    <a href="{{{{% url '{APP_NAME}:{model_name_lower}_delete' obj.pk %}}}}" class="btn btn-sm btn-danger">Löschen</a>
                </td>
            </tr>
        {{% endfor %}}
        </tbody>
    </table>
    {{% endblock %}}
    """
    write_file(os.path.join(TEMPLATES_DIR, f"{model_name_lower}_list.html"), list_template)

# Forms generieren
forms_content = "from django import forms\nfrom .models import *\n\n"
for model_name, fields in models.items():
    form_fields = [f"'{field[0]}'" for field in fields]
    forms_content += f"class {model_name}Form(forms.ModelForm):\n"
    forms_content += f"    class Meta:\n        model = {model_name}\n"
    forms_content += f"        fields = [{', '.join(form_fields)}]\n\n"
write_file(FORMS_PATH, forms_content)

# Views generieren
views_content = "from django.views.generic import ListView, DetailView, CreateView, DeleteView, TemplateView\n"
views_content += "from django.urls import reverse_lazy\nfrom .models import *\nfrom .forms import *\n\n"

views_content += "class IndexView(TemplateView):\n    template_name = 'index.html'\n\n"

for model_name in models.keys():
    model_name_lower = model_name.lower()
    views_content += f"""
class {model_name}ListView(ListView):
    model = {model_name}
    template_name = '{model_name_lower}_list.html'
    context_object_name = 'object_list'

class {model_name}CreateView(CreateView):
    model = {model_name}
    form_class = {model_name}Form
    template_name = '{model_name_lower}_form.html'

class {model_name}DeleteView(DeleteView):
    model = {model_name}
    template_name = '{model_name_lower}_confirm_delete.html'
    success_url = reverse_lazy('{APP_NAME}:{model_name_lower}_list')
"""
write_file(VIEWS_PATH, views_content)

# URLs generieren
urls_content = "from django.urls import path\nfrom .views import *\n\n"
urls_content += f"app_name = '{APP_NAME}'\n\nurlpatterns = [\n"
urls_content += "    path('', IndexView.as_view(), name='index'),\n"

for model_name in models.keys():
    model_name_lower = model_name.lower()
    urls_content += f"    path('{model_name_lower}/', {model_name}ListView.as_view(), name='{model_name_lower}_list'),\n"
    urls_content += f"    path('{model_name_lower}/create/', {model_name}CreateView.as_view(), name='{model_name_lower}_create'),\n"

urls_content += "]\n"
write_file(URLS_PATH, urls_content)

print("CRUD erfolgreich generiert!")
