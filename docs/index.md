---
title: "Jyotisha py site"
---

Welcome!

{% for post in site.pages %}
<a href="{{ site.url }}{{ post.url }}">{{ site.url }}{{ post.url }}</a>
{% endfor %}