import os
import glob
import re

template_dir = 'parking/templates/parking'
files = glob.glob(os.path.join(template_dir, '*.html'))

language_switcher = """
<div class="px-6 mt-auto mb-4">
    <form action="{% url 'set_language' %}" method="post" class="flex gap-2">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <select name="language" onchange="this.form.submit()" class="text-sm bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2">
            {% get_current_language as LANGUAGE_CODE %}
            {% get_available_languages as LANGUAGES %}
            {% get_language_info_list for LANGUAGES as languages %}
            {% for language in languages %}
                <option value="{{ language.code }}"{% if language.code == LANGUAGE_CODE %} selected{% endif %}>
                    {{ language.name_local|title }}
                </option>
            {% endfor %}
        </select>
    </form>
</div>
</nav>
"""

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add load i18n
    if '{% load i18n %}' not in content:
        content = '{% load i18n %}\n' + content
        
    # Replace the side nav bar texts
    content = content.replace('>Dashboard<', '>{% trans "Dashboard" %}<')
    content = content.replace('>Buscador<', '>{% trans "Buscador" %}<')
    content = content.replace('>Parkings<', '>{% trans "Parkings" %}<')
    content = content.replace('>Space Management<', '>{% trans "Space Management" %}<')
    content = content.replace('>Vehicle Registry<', '>{% trans "Vehicle Registry" %}<')
    content = content.replace('>Rates &amp; Billing<', '>{% trans "Rates &amp; Billing" %}<')
    content = content.replace('>Analíticas<', '>{% trans "Analíticas" %}<')
    
    # Add language switcher before closing nav
    if 'name="language"' not in content:
        content = content.replace('</nav>', language_switcher)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Processed templates.")
