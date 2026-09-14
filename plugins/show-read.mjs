const READ_PAIR = /^(.*?)\s*<([^<>]+)>\s*$/;

const showReadDirective = {
  name: 'show-read',
  doc: 'Show the body on the page. The :read: option is the spoken paragraph for a Reading.',
  options: {
    read: {
      type: String,
      doc: 'Spoken text for the Reading. If omitted, the body is spoken.',
    },
  },
  body: {
    type: 'myst',
    required: true,
    doc: 'Text shown on the page.',
  },
  run(data) {
    const children = data.body;
    if (Array.isArray(children) && children.length) {
      return children;
    }
    return [];
  },
};

const readRole = {
  name: 'read',
  doc: 'Show the first span on the page. Text in angle brackets is spoken in a Reading.',
  body: {
    type: String,
    required: true,
    doc: 'Page text, then spoken text in angle brackets, for example O(N²) <O of N squared>.',
  },
  run(data) {
    const raw = String(data.body ?? '').trim();
    const match = READ_PAIR.exec(raw);
    const show = (match ? match[1] : raw).trim();
    return [{ type: 'text', value: show }];
  },
};

const plugin = {
  name: 'Show and read',
  directives: [showReadDirective],
  roles: [readRole],
};

export default plugin;
