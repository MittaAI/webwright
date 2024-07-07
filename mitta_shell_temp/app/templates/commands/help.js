// help.js
// line: help for mitta's command line interface
// command: !help
// author: kordless@gmail.com
// copyright: all rights reserved, 2022
// help.js
const { timestamp, line, command } = window.mittaBase;

// There are reasons why Data didn't use contractions
Sidekick("Get Started\n===========", hide_prompt=true);
Sidekick("<i><a href command='!keyboard' id='keyboard-{{target_id}}'>!keyboard</a></i> for how to use the UI.", hide_prompt=true);
Sidekick("<i><a href command='!help' id='help-{{target_id}}'>!help</a></i> show the help.", hide_prompt=true);
Sidekick("<i><a href command='!logout' id='logout-{{target_id}}'>!logout</a></i> from the system.", hide_prompt=true);
Sidekick("<i><a href command='!settings' id='settings-{{target_id}}'>!settings</a></i> for your account.", hide_prompt=true);
Sidekick("<i><a href completion='!openai |token [token]' id='openai-{{target_id}}'>!openai |token</a></i> to set your OpenAI token.", hide_prompt=true);
Sidekick("<i><a href command='!history' id='history-{{target_id}}'>!history</a></i> of entries.", hide_prompt=true);
Sidekick("&nbsp;", hide_prompt=true)
Sidekick("Browser Control\n===============", hide_prompt=true);
Sidekick("<i><a href command='!map Australia' id='gm-{{target_id}}'>!map</a></i> of Australia.", hide_prompt=true);
Sidekick("<i><a href command='!open slashdot' id='slashdot-{{target_id}}'>!open</a></i> by name or URL.", hide_prompt=true);
Sidekick("<i><a href command='!sms hello' id='sms-{{target_id}}'>!sms</a></i> to send to phone.", hide_prompt=true);
Sidekick("<i><a href command='!calc sqrt of pi' id='calc-{{target_id}}'>!calc</a></i> writes code and does math.", hide_prompt=true);
Sidekick("&nbsp;", hide_prompt=true)
Sidekick("Upload or Crawl\n===============", hide_prompt=true);
Sidekick("<i><a href command='!crawl https://slashdot.org/' id='crawl-{{target_id}}'>!crawl</a></i> and index a URL.", hide_prompt=true);
Sidekick("<i><a href command='!upload' id='upload-{{target_id}}'>!upload</a></i> images and tag them.</i>", hide_prompt=true);
Sidekick("<i><a href command='!sidekick |help' id='sidekick-{{target_id}}'>!sidekick |help</a></i> shows sidekick methods.", hide_prompt=true);
Sidekick("<i><a href command='!plugin' id='plugin-{{target_id}}'>!plugin</a></i> will save pages you visit.", hide_prompt=true);
Sidekick("&nbsp;", hide_prompt=true)
Sidekick("Finding and Discussing\n=======================", hide_prompt=true);
Sidekick("<i><a href command='!search slashdot' id='mitta-{{target_id}}'>!search &lt;term&gt;</a></i> searches your documents.", hide_prompt=true);
Sidekick("<i><a href command='!google pliers' id='google-{{target_id}}'>!google</a></i> searches Google for new documents.", hide_prompt=true);
Sidekick("<i><a href command='!discuss what is philosophy?' id='text-{{target_id}}'>!discuss</a></i> one of your documents.", hide_prompt=true);
Sidekick("&nbsp;", hide_prompt=true)
Sidekick("You can <i><a href command='!guide' id='guide-{{target_id}}'>view the guide</a></i> or just start talking to me.", hide_prompt=false);

// return app_id to eval
"{{app_id}}";