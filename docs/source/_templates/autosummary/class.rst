{% extends "!autosummary/class.rst" %}

{% block methods %}
   {% set methods = methods | select("ne", "__init__") | list %}
   {% if methods %}
   .. rubric:: Methods

   .. autosummary::
   {% for item in methods %}
   {%- if item not in inherited_members %}
         ~{{ name }}.{{ item }}
   {%- endif %}
   {%- endfor %}

   {% endif %}

{% endblock %}

{% block attributes %}
   {% if attributes %}
   .. rubric:: Attributes

   .. autosummary::
   {% for item in attributes %}
   {%- if item not in inherited_members %}
         ~{{ name }}.{{ item }}
   {%- endif %}
   {%- endfor %}

   {% endif %}

{% endblock %}