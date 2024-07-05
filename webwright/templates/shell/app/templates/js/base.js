// base.js
window.mittaBase = {
    timestamp: '{{timestamp}}',
    line: `{{line|safe}}`,
    command: '{{command}}',
    strip_command: `{{strip_command|safe}}`,
    timeword: '{{timeword}}',
    timewords: {{timewords|tojson}},
    view: '{{view}}',
    username: '{{username}}',
    nick: '{{nick}}',
    engine: '{{engine}}',
    mode: '{{mode}}',
    document_id: '{{document_id}}',
    text: `{{text|safe}}`,
    tags: {{tags|tojson}},
    offsets: {{offsets|tojson}},
    fields_dictionary: {{fields_dictionary|tojson}},
    text_and_fields: `{{text_and_fields|safe}}`,
    text_plus_url: `{{text_plus_url|safe}}`,
    url: '{{url|safe}}',
    url_unencoded: '{{url_unencoded|safe}}',
    sidekick: '{{sidekick_nick}}',
    spool: "",
    mood: '{{mood}}',
    moods: {{moods|tojson}},
    numDocs: '{{num_docs}}',
    rollup_HTML: "",
    rollup_clicks: []
};

console.log('all your base loaded');