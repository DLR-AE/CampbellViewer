{{ name | escape | underline(line='#') }}
*{{ fullname }}*

.. currentmodule:: {{ module }}

{% block methods %}
{% if methods %}

{{ "Methods" | escape | underline }}

.. tab-set::

   .. tab-item:: Plain
      :sync: key-plain

      .. autosummary::
{% for item in methods %}
{%- if item not in inherited_members %}
         ~{{ name }}.{{ item }}
{% endif %}
{%- endfor %}

   .. tab-item:: Inherited
      :sync: key-inherited

      .. autosummary::
{% for item in methods %}
{%- if item in inherited_members %}
         ~{{ name }}.{{ item }}
{% endif %}
{%- endfor %}
{% endif %}
{% endblock %}


{% block attributes %}
{% if attributes %}

{{ "Attributes" | escape | underline }}

.. tab-set::

   .. tab-item:: Plain
      :sync: key-plain

      .. autosummary::
{% for item in attributes %}
{%- if item not in inherited_members %}
         ~{{ name }}.{{ item }}
{% endif %}
{%- endfor %}

   .. tab-item:: Inherited
      :sync: key-inherited

      .. autosummary::
{% for item in attributes %}
{%- if item in inherited_members %}
         ~{{ name }}.{{ item }}
{% endif %}
{%- endfor %}
{% endif %}
{% endblock %}


{% set ns = namespace(prev="") %}
{% for item in methods %}
{%- if item not in inherited_members %}
{% set ns.prev = ns.prev + name + "." + item  + "," %}
{% endif %}
{%- endfor %}


{{ "Definition" | escape | underline }}

.. tab-set::

   .. tab-item:: Plain
      :sync: key-plain

      .. autoclass:: {{ objname }}
         :show-inheritance:
         :members: {{ ns.prev }}

   .. tab-item:: Inherited
      :sync: key-inherited

      .. autoclass:: {{ objname }}
         :show-inheritance:
         :inherited-members:
         :noindex:
