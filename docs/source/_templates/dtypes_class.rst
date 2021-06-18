{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. automodule:: {{ fullname }}
   :members:
   :member-order: bysource
   :show-inheritance:
   :exclude-members:

   {% block classes %}

     {% for item in classes %}
        .. autoclass:: {{ item }}
           :members:
           :member-order: bysource
           :show-inheritance:
           :exclude-members:
     {%- endfor %}

   {% endblock %}

   {% block functions %}

     {% for item in functions %}
        .. autofunction:: {{ item }}
     {%- endfor %}

   {% endblock %}
