---
title: "Jyotisha py site"
---

Welcome!

{% for post in site.pages %}
<a href="{{ site.url }}{{ site.baseurl }}{{ post.url }}">{{ post.url }}</a>
{% endfor %}