{{ name | escape | underline(line='#') }}
*{{ fullname }}*

.. automodule:: {{ fullname }}
   :no-members:

{% block attributes %}
{% if attributes %}
{{ "Module Attributes" | escape | underline(line='^') }}

.. autosummary::
   :toctree:
{% for item in attributes %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block functions %}
{% if functions %}
{{ "Functions" | escape | underline(line='^') }}

.. autosummary::
   :toctree:
{% for item in functions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block classes %}
{% if classes %}
{{ "Classes" | escape | underline(line='^') }}

.. autosummary::
   :toctree:
   :template: custom-class-template.rst
   :recursive:
{% for item in classes %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block exceptions %}
{% if exceptions %}
{{ "Exceptions" | escape | underline(line='^') }}

.. autosummary::
   :toctree:
{% for item in exceptions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block modules %}
{% if modules %}
{{ "Modules" | escape | underline(line='^') }}

.. autosummary::
   :toctree:
   :template: custom-module-template.rst
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}
