// notfound.js
// This script is executed when a command is not found

// Access the base variables
const { timestamp, username, mode } = window.mittaBase;

// Get the specific command variables
const app_id = "{{app_id}}";
const target_id = "{{target_id}}";
const line = `{{line}}`;
const command = "{{command}}";

// Construct the response
let response = '';
response += Sidekick(`I'm sorry, but I couldn't find the command "${command}".`);
response += Sidekick("Here are some things you can try:", true);
response += Sidekick("1. Check the spelling of your command.", true);
response += Sidekick("2. Type <a href command='!help' id='help-link-${app_id}'>!help</a> to see a list of available commands.", true);
response += Sidekick("3. If you think this is a bug, please report it to the developers.", true);

// Send the response back to the client
const result = {
    app_id: app_id,
    target_id: target_id,
    html: response,
    js: `
        // Any additional JavaScript you want to run on the client side
        console.log("Command not found: " + "${command}");
    `
};

// Return the result as a JSON string
JSON.stringify(result);