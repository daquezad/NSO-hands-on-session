{# Story 6.3 — print-site cover; context: config (MkDocs), page (print page). #}
<div class="pdf-cover">
  <div class="pdf-cover__classification" role="status">Cisco Confidential</div>
  {% if config.site_name %}
  <h1 class="pdf-cover__title">{{ config.site_name }}</h1>
  {% endif %}
  <p class="pdf-cover__meta">
    <strong>
      NSO
      {% if config.extra and config.extra.nso_version %}
      {{ config.extra.nso_version }}
      {% else %}
      —
      {% endif %}
    </strong>
  </p>
  {% if config.extra and config.extra.pdf_build_date %}
  <p class="pdf-cover__meta pdf-cover__meta--date">
    <strong>Build date (UTC)</strong> {{ config.extra.pdf_build_date }}
  </p>
  {% endif %}
  {% if config.extra and config.extra.bug_report_url %}
  <p class="pdf-cover__bug">
    <a class="pdf-cover__bug-link" href="{{ config.extra.bug_report_url }}">Report an issue</a>
  </p>
  {% endif %}
</div>
