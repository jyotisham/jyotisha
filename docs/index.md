---
title: "Jyotisha py site"
---

Welcome!

## Calendar Output
{% for p in site.pages %}
{% if p.url contains "output" %}
<a href="{{ p.url | absolute_url}}">{{ p.url | url_decode}}</a>
{% endif %}
{% endfor %}

## ICS iCalendar files
{% for p in site.pages %}
{% if p.url contains "output" %}
<a href="{{ p.url | absolute_url| replace: ".html", ".ics"}}">{{ p.url | url_decode| replace: ".html", ".ics"}}</a>
{% endif %}
{% endfor %}
